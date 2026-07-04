#include <atomic>
#include <chrono>
#include <condition_variable>
#include <csignal>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <mutex>
#include <regex>
#include <string>
#include <thread>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

extern "C" {
#include "msp_cmn.h"
#include "msp_errors.h"
#include "qisr.h"
#include "linuxrec.h"
#include "speech_recognizer.h"
}

extern "C" int sr_init_ex(struct speech_rec *sr, const char *session_begin_params,
                          enum sr_audsrc aud_src, record_dev_id devid,
                          struct speech_rec_notifier *notify);

namespace {

constexpr int kSampleRate = 16000;
constexpr int kMaxGrammarIdLen = 32;
constexpr int kMaxParamsLen = 1024;

struct GrammarData {
  int build_done = 0;
  int errcode = MSP_SUCCESS;
  char grammar_id[kMaxGrammarIdLen] = {0};
};

std::atomic_bool g_running{true};

std::string read_file(const std::string &path) {
  std::ifstream in(path, std::ios::binary);
  return std::string((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
}

int build_grammar_cb(int ecode, const char *info, void *userdata) {
  auto *data = static_cast<GrammarData *>(userdata);
  if (!data) {
    return 0;
  }
  data->build_done = 1;
  data->errcode = ecode;
  if (ecode == MSP_SUCCESS && info) {
    std::snprintf(data->grammar_id, sizeof(data->grammar_id), "%s", info);
  }
  return 0;
}

std::string extract_rawtext(const std::string &xml) {
  std::smatch match;
  static const std::regex rawtext_re("<rawtext>(.*?)</rawtext>", std::regex::icase);
  if (std::regex_search(xml, match, rawtext_re) && match.size() > 1) {
    return match[1].str();
  }
  return {};
}

struct RecognitionState {
  std::mutex mutex;
  std::condition_variable cv;
  std::string result_xml;
  bool finished = false;
  int end_reason = 0;
};

RecognitionState g_recognition_state;

void on_result(const char *result, char is_last) {
  if (!result) {
    return;
  }
  {
    std::lock_guard<std::mutex> lock(g_recognition_state.mutex);
    g_recognition_state.result_xml += result;
    if (is_last) {
      g_recognition_state.finished = true;
    }
  }
  g_recognition_state.cv.notify_all();
}

void on_speech_begin() {
  std::lock_guard<std::mutex> lock(g_recognition_state.mutex);
  g_recognition_state.result_xml.clear();
  g_recognition_state.finished = false;
  g_recognition_state.end_reason = 0;
}

void on_speech_end(int reason) {
  {
    std::lock_guard<std::mutex> lock(g_recognition_state.mutex);
    g_recognition_state.end_reason = reason;
    g_recognition_state.finished = true;
  }
  g_recognition_state.cv.notify_all();
}

void signal_handler(int) {
  g_running = false;
}

}  // namespace

class IflytekAsrBridge : public rclcpp::Node {
 public:
  IflytekAsrBridge() : Node("iflytek_asr_bridge") {
    appid_ = declare_parameter<std::string>("appid", "df41b4a2");
    sdk_dir_ = declare_parameter<std::string>("sdk_dir", "/mnt/sdcard/iflytek_tts_df41b4a2/bin");
    asr_res_path_ = declare_parameter<std::string>("asr_res_path", "fo|res/asr/common.jet");
    grammar_file_ = declare_parameter<std::string>("grammar_file", "call.bnf");
    grammar_build_path_ = declare_parameter<std::string>("grammar_build_path", "res/asr/GrmBuilld");
    recognition_mode_ = declare_parameter<std::string>("recognition_mode", "grammar");
    capture_device_ = declare_parameter<std::string>("capture_device", "plughw:CARD=XFMDPV0018,DEV=0");
    listen_seconds_ = declare_parameter<int>("listen_seconds", 8);
    pause_ms_ = declare_parameter<int>("pause_ms", 500);
    min_confidence_ = declare_parameter<int>("min_confidence", 0);

    voice_words_pub_ = create_publisher<std_msgs::msg::String>("/voice_words", 10);
    asr_text_pub_ = create_publisher<std_msgs::msg::String>("/medicine/asr_text", 10);

    worker_ = std::thread([this]() { run(); });
  }

  ~IflytekAsrBridge() override {
    g_running = false;
    if (worker_.joinable()) {
      worker_.join();
    }
    MSPLogout();
  }

 private:
  bool build_grammar(GrammarData *data) {
    const std::string content = read_file(grammar_file_);
    if (content.empty()) {
      RCLCPP_ERROR(get_logger(), "Grammar file is empty or missing: %s", grammar_file_.c_str());
      return false;
    }

    char params[kMaxParamsLen] = {0};
    std::snprintf(params, sizeof(params) - 1,
                  "engine_type = local, asr_res_path = %s, sample_rate = %d, grm_build_path = %s, ",
                  asr_res_path_.c_str(), kSampleRate, grammar_build_path_.c_str());

    int ret = QISRBuildGrammar("bnf", content.c_str(), static_cast<unsigned int>(content.size()),
                               params, build_grammar_cb, data);
    if (ret != MSP_SUCCESS) {
      RCLCPP_ERROR(get_logger(), "QISRBuildGrammar call failed: %d", ret);
      return false;
    }

    while (rclcpp::ok() && g_running && data->build_done != 1) {
      std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
    if (data->errcode != MSP_SUCCESS) {
      RCLCPP_ERROR(get_logger(), "QISRBuildGrammar failed: %d", data->errcode);
      return false;
    }
    RCLCPP_INFO(get_logger(), "ASR grammar built, id=%s", data->grammar_id);
    return true;
  }

  void run() {
    if (chdir(sdk_dir_.c_str()) != 0) {
      RCLCPP_ERROR(get_logger(), "chdir sdk_dir failed: %s", sdk_dir_.c_str());
      return;
    }

    const std::string login = "appid = " + appid_ + ", work_dir = .";
    int ret = MSPLogin(nullptr, nullptr, login.c_str());
    if (ret != MSP_SUCCESS) {
      RCLCPP_ERROR(get_logger(), "MSPLogin failed: %d", ret);
      return;
    }

    char session_params[kMaxParamsLen] = {0};
    if (recognition_mode_ == "iat") {
      std::snprintf(session_params, sizeof(session_params) - 1,
                    "sub = iat, domain = iat, language = zh_cn, accent = mandarin, "
                    "sample_rate = %d, result_type = plain, result_encoding = UTF-8",
                    kSampleRate);
      RCLCPP_INFO(get_logger(), "ASR mode: online/free dictation IAT");
    } else {
      GrammarData grammar;
      if (!build_grammar(&grammar)) {
        return;
      }
      std::snprintf(session_params, sizeof(session_params) - 1,
                    "engine_type = local, asr_res_path = %s, sample_rate = %d, "
                    "grm_build_path = %s, local_grammar = %s, result_type = xml, result_encoding = UTF-8, ",
                    asr_res_path_.c_str(), kSampleRate, grammar_build_path_.c_str(),
                    grammar.grammar_id);
      RCLCPP_INFO(get_logger(), "ASR mode: local grammar");
    }

    RCLCPP_INFO(get_logger(), "iFlytek ASR bridge listening on %s.", capture_device_.c_str());

    while (rclcpp::ok() && g_running) {
      listen_once(session_params);
      std::this_thread::sleep_for(std::chrono::milliseconds(pause_ms_));
    }
  }

  void listen_once(const char *session_params) {
    {
      std::lock_guard<std::mutex> lock(g_recognition_state.mutex);
      g_recognition_state.result_xml.clear();
      g_recognition_state.finished = false;
      g_recognition_state.end_reason = 0;
    }

    speech_rec recognizer;
    speech_rec_notifier notifier;
    notifier.on_result = on_result;
    notifier.on_speech_begin = on_speech_begin;
    notifier.on_speech_end = on_speech_end;

    record_dev_id capture_device;
    capture_device.u.name = const_cast<char *>(capture_device_.c_str());
    int err = sr_init_ex(&recognizer, session_params, SR_MIC, capture_device, &notifier);
    if (err != 0) {
      RCLCPP_WARN(get_logger(), "sr_init failed: %d", err);
      return;
    }

    err = sr_start_listening(&recognizer);
    if (err != 0) {
      RCLCPP_WARN(get_logger(), "sr_start_listening failed: %d", err);
      sr_uninit(&recognizer);
      return;
    }

    {
      std::unique_lock<std::mutex> lock(g_recognition_state.mutex);
      g_recognition_state.cv.wait_for(
          lock,
          std::chrono::seconds(listen_seconds_),
          []() { return g_recognition_state.finished || !g_running.load(); });
    }

    err = sr_stop_listening(&recognizer);
    if (err != 0) {
      RCLCPP_WARN(get_logger(), "sr_stop_listening failed: %d", err);
    }
    sr_uninit(&recognizer);

    std::string result_xml;
    {
      std::lock_guard<std::mutex> lock(g_recognition_state.mutex);
      result_xml = g_recognition_state.result_xml;
    }

    std::string raw;
    if (recognition_mode_ == "iat") {
      raw = result_xml;
    } else {
      raw = extract_rawtext(result_xml);
    }
    if (raw.empty()) {
      RCLCPP_INFO(get_logger(), "ASR got no text. end_reason=%d", g_recognition_state.end_reason);
      return;
    }

    std_msgs::msg::String msg;
    msg.data = raw;
    voice_words_pub_->publish(msg);
    asr_text_pub_->publish(msg);
    RCLCPP_INFO(get_logger(), "ASR recognized: %s", raw.c_str());
  }

  std::string appid_;
  std::string sdk_dir_;
  std::string asr_res_path_;
  std::string grammar_file_;
  std::string grammar_build_path_;
  std::string recognition_mode_;
  std::string capture_device_;
  int listen_seconds_;
  int pause_ms_;
  int min_confidence_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr voice_words_pub_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr asr_text_pub_;
  std::thread worker_;
};

int main(int argc, char **argv) {
  std::signal(SIGINT, signal_handler);
  std::signal(SIGTERM, signal_handler);
  rclcpp::init(argc, argv);
  auto node = std::make_shared<IflytekAsrBridge>();
  rclcpp::spin(node);
  g_running = false;
  rclcpp::shutdown();
  return 0;
}
