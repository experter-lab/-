import json
import os
import queue
import re
import threading
import time
import urllib.error
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class AiVoiceChatBridgeNode(Node):
    def __init__(self):
        super().__init__("medicine_ai_voice_chat_bridge")
        self.declare_parameter("voice_words_topic", "/voice_words")
        self.declare_parameter("manual_chat_topic", "/medicine/ai_chat_text")
        self.declare_parameter("chat_message_topic", "/chat_message")
        self.declare_parameter("vision_context_topic", "/medicine/vision_drug_context")
        self.declare_parameter("patient_context_topic", "/medicine/patient_voice_context")
        self.declare_parameter("patient_context_ttl_sec", 420.0)
        self.declare_parameter("use_vision_context_when_patient_context_active", False)
        self.declare_parameter("chat_response_topic", "/chat_response")
        self.declare_parameter("ai_response_topic", "/medicine/ai_chat_response")
        self.declare_parameter("voice_topic", "/medicine/voice_text")
        self.declare_parameter("base_url", "http://127.0.0.1:11434/v1")
        self.declare_parameter("api_key", "")
        self.declare_parameter("use_model", "deepseek-r1")
        self.declare_parameter("temperature", 0.4)
        self.declare_parameter("timeout_sec", 60.0)
        self.declare_parameter("history_length", 8)
        self.declare_parameter("queue_size", 8)
        self.declare_parameter("max_input_chars", 240)
        self.declare_parameter("max_reply_chars", 220)
        self.declare_parameter("max_tokens", 160)
        self.declare_parameter("deduplicate_window_sec", 4.0)
        self.declare_parameter("echo_filter_window_sec", 90.0)
        self.declare_parameter("echo_similarity_threshold", 0.68)
        self.declare_parameter("mic_post_answer_guard_sec", 8.0)
        self.declare_parameter("mic_repeat_suppress_sec", 45.0)
        self.declare_parameter("mic_require_intent", True)
        self.declare_parameter("mic_fragment_merge_sec", 2.2)
        self.declare_parameter("mic_fragment_max_chars", 36)
        self.declare_parameter("respond_to_wake_word_only", True)
        self.declare_parameter("strip_think_tags", True)
        self.declare_parameter("publish_voice", True)
        self.declare_parameter("voice_prefix", "")
        self.declare_parameter("enable_knowledge_base", True)
        self.declare_parameter("knowledge_dir", "/mnt/sdcard/medicine_robot_data/knowledge")
        self.declare_parameter("knowledge_max_chunks", 5)
        self.declare_parameter("knowledge_max_chars", 1800)
        self.declare_parameter("knowledge_min_score", 3.0)
        self.declare_parameter(
            "system_prompt",
            "You are Xiao Yao Zhu, a voice assistant on a hospital medicine-delivery robot. "
            "Always reply in concise, warm Chinese suitable for elderly patients. "
            "Use one to three short spoken sentences, not bullet points or list formatting. "
            "Avoid repeating the same warning or explanation. "
            "Prefer a direct answer first, then one brief reminder. "
            "Never ramble or restate the same point in different words. "
            "You are a robot, not a nurse, family member, or human caregiver. State capability boundaries clearly. "
            "You may read the current delivery medicines, explain medication instructions already present in the task/page, remind identity and medicine checks, and advise the patient to press the nurse call button or contact a nurse, doctor, or pharmacist. "
            "You must not promise physical nursing actions: arranging medicines, pouring water, preparing warm water, lifting or supporting a patient, feeding medicine, taking medicine for the patient, direct clinical care, personally contacting a nurse, or guaranteeing all medicines are correct. "
            "If asked to do those actions, say you cannot directly do that action, then suggest asking a nurse/family member or pressing the call button. "
            "Usually answer in two to four short sentences. Do not diagnose, invent dose, or suggest stopping/changing medication. "
            "If medicine name, prescription, or instruction is unclear, do not guess timing, meal relation, or tablet count. "
            "For chest pain, breathing difficulty, confusion, heavy bleeding, allergy, pregnancy/children/elderly complex medication, or polypharmacy, gently but clearly advise contacting medical staff. Do not reveal reasoning.",
        )
        self.declare_parameter("trigger_prefixes", "")

        self.voice_words_topic = self.string_param("voice_words_topic")
        self.manual_chat_topic = self.string_param("manual_chat_topic")
        self.chat_message_topic = self.string_param("chat_message_topic")
        self.vision_context_topic = self.string_param("vision_context_topic")
        self.patient_context_topic = self.string_param("patient_context_topic")
        self.patient_context_ttl_sec = float(self.get_parameter("patient_context_ttl_sec").value)
        self.use_vision_context_when_patient_context_active = bool(self.get_parameter("use_vision_context_when_patient_context_active").value)
        self.chat_response_topic = self.string_param("chat_response_topic")
        self.ai_response_topic = self.string_param("ai_response_topic")
        self.voice_topic = self.string_param("voice_topic")
        self.base_url = self.string_param("base_url").rstrip("/")
        self.api_key = self.string_param("api_key") or os.environ.get("AI_CHAT_API_KEY", "ollama")
        self.use_model = self.string_param("use_model")
        self.temperature = self.get_parameter("temperature").get_parameter_value().double_value
        self.timeout_sec = self.get_parameter("timeout_sec").get_parameter_value().double_value
        self.history_length = int(self.get_parameter("history_length").value)
        self.max_input_chars = int(self.get_parameter("max_input_chars").value)
        self.max_reply_chars = int(self.get_parameter("max_reply_chars").value)
        self.max_tokens = int(self.get_parameter("max_tokens").value)
        self.deduplicate_window_sec = float(self.get_parameter("deduplicate_window_sec").value)
        self.echo_filter_window_sec = float(self.get_parameter("echo_filter_window_sec").value)
        self.echo_similarity_threshold = float(self.get_parameter("echo_similarity_threshold").value)
        self.mic_post_answer_guard_sec = float(self.get_parameter("mic_post_answer_guard_sec").value)
        self.mic_repeat_suppress_sec = float(self.get_parameter("mic_repeat_suppress_sec").value)
        self.mic_require_intent = bool(self.get_parameter("mic_require_intent").value)
        self.mic_fragment_merge_sec = float(self.get_parameter("mic_fragment_merge_sec").value)
        self.mic_fragment_max_chars = int(self.get_parameter("mic_fragment_max_chars").value)
        self.respond_to_wake_word_only = bool(self.get_parameter("respond_to_wake_word_only").value)
        self.strip_think_tags = bool(self.get_parameter("strip_think_tags").value)
        self.publish_voice = bool(self.get_parameter("publish_voice").value)
        self.voice_prefix = self.string_param("voice_prefix")
        self.enable_knowledge_base = bool(self.get_parameter("enable_knowledge_base").value)
        self.knowledge_dir = self.string_param("knowledge_dir")
        self.knowledge_max_chunks = int(self.get_parameter("knowledge_max_chunks").value)
        self.knowledge_max_chars = int(self.get_parameter("knowledge_max_chars").value)
        self.knowledge_min_score = float(self.get_parameter("knowledge_min_score").value)
        self.system_prompt = self.string_param("system_prompt")
        self.trigger_prefixes = [
            item.strip()
            for item in self.string_param("trigger_prefixes").split(",")
            if item.strip()
        ]

        max_queue = max(1, int(self.get_parameter("queue_size").value))
        self.pending = queue.Queue(maxsize=max_queue)
        self.history = [{"role": "system", "content": self.system_prompt}]
        self.last_text = ""
        self.last_time = 0.0
        self.recent_answers = []
        self.recent_mic_questions = {}
        self.last_answer_time = 0.0
        self.mic_fragment_buffer = []
        self.mic_fragment_first_at = 0.0
        self.mic_fragment_last_at = 0.0
        self.running = True
        self.latest_vision_context = ""
        self.latest_vision_context_at = 0.0
        self.latest_patient_context = None
        self.latest_patient_context_at = 0.0
        self.knowledge_chunks = []
        if self.enable_knowledge_base:
            self.load_knowledge_base()

        self.voice_pub = self.create_publisher(String, self.voice_topic, 10)
        self.ai_response_pub = self.create_publisher(String, self.ai_response_topic, 10)
        self.chat_response_pub = self.create_publisher(String, self.chat_response_topic, 10)
        self.create_subscription(String, self.voice_words_topic, self.on_voice_words, 10)
        self.create_subscription(String, self.manual_chat_topic, self.on_manual_chat, 10)
        self.create_subscription(String, self.vision_context_topic, self.on_vision_context, 10)
        self.create_subscription(String, self.patient_context_topic, self.on_patient_context, 10)
        if self.chat_message_topic not in {self.voice_words_topic, self.manual_chat_topic}:
            self.create_subscription(String, self.chat_message_topic, self.on_chat_message, 10)

        self.worker = threading.Thread(target=self.chat_worker, daemon=True)
        self.worker.start()
        self.create_timer(0.2, self.flush_mic_fragments_if_ready)
        self.get_logger().info(
            "AI voice chat bridge started. "
            f"voice_words={self.voice_words_topic}, manual={self.manual_chat_topic}, "
            f"model={self.use_model}, base_url={self.base_url}, "
            f"knowledge_chunks={len(self.knowledge_chunks)}"
        )

    def string_param(self, name):
        return self.get_parameter(name).get_parameter_value().string_value

    def on_voice_words(self, msg):
        text = self.clean_text(msg.data)
        if not text:
            return
        if self.trigger_prefixes:
            matched = False
            for prefix in self.trigger_prefixes:
                if text.startswith(prefix):
                    text = text[len(prefix):].strip(" ?,?")
                    matched = True
                    break
            if not matched or not text:
                return
        self.handle_mic_fragment(text)

    def handle_mic_fragment(self, text):
        cleaned = self.clean_text(text)
        if not cleaned:
            return
        now = time.monotonic()
        normalized = self.normalize_echo_text(cleaned)
        fragment_has_intent = self.is_meaningful_mic_input(cleaned)
        should_buffer = (
            self.mic_fragment_merge_sec > 0.0
            and len(normalized) <= max(4, self.mic_fragment_max_chars)
            and not fragment_has_intent
            and not cleaned.endswith(("?", "?", "?", "!"))
        )
        if not self.mic_fragment_buffer:
            self.mic_fragment_first_at = now
        self.mic_fragment_buffer.append(cleaned)
        self.mic_fragment_last_at = now
        merged = self.merge_mic_fragments()
        if not should_buffer or self.is_meaningful_mic_input(merged) or len(self.normalize_echo_text(merged)) >= self.mic_fragment_max_chars:
            self.flush_mic_fragments(force=True)

    def merge_mic_fragments(self):
        parts = [self.clean_text(item).strip(" ?,?") for item in self.mic_fragment_buffer if self.clean_text(item)]
        if not parts:
            return ""
        return self.clean_text("".join(parts))

    def flush_mic_fragments_if_ready(self):
        if not self.mic_fragment_buffer:
            return
        if time.monotonic() - self.mic_fragment_last_at >= self.mic_fragment_merge_sec:
            self.flush_mic_fragments(force=True)

    def flush_mic_fragments(self, force=False):
        if not self.mic_fragment_buffer:
            return
        merged = self.merge_mic_fragments()
        self.mic_fragment_buffer = []
        self.mic_fragment_first_at = 0.0
        self.mic_fragment_last_at = 0.0
        if not merged:
            return
        self.enqueue_chat(merged, "mic")
    def on_manual_chat(self, msg):
        text = self.clean_text(msg.data)
        if text:
            self.enqueue_chat(text, "manual")

    def on_chat_message(self, msg):
        text = self.extract_chat_content(msg.data)
        if text:
            self.enqueue_chat(text, "chat_message")

    def on_vision_context(self, msg):
        text = self.clean_text(msg.data)
        if not text:
            return
        self.latest_vision_context = text
        self.latest_vision_context_at = time.time()
        self.get_logger().info(f"Vision context updated: {text}")

    def on_patient_context(self, msg):
        raw = str(msg.data or "").strip()
        if not raw:
            return
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            self.get_logger().warn("Invalid patient context JSON")
            return
        if not isinstance(payload, dict):
            return
        self.latest_patient_context = payload
        self.latest_patient_context_at = time.time()
        bed = payload.get("bed") or ""
        drug_count = len(payload.get("drugs") or [])
        self.get_logger().info(f"Patient voice context updated: bed={bed}, drugs={drug_count}")

    def build_patient_context_prompt(self):
        context = self.latest_patient_context
        if not isinstance(context, dict):
            return ""
        age = time.time() - self.latest_patient_context_at
        if age > self.patient_context_ttl_sec:
            self.get_logger().info(
                f"Patient voice context expired: age={age:.1f}s ttl={self.patient_context_ttl_sec:.1f}s"
            )
            return ""
        lines = ["\u5f53\u524d\u75c5\u4eba\u8bed\u97f3\u4f1a\u8bdd\u4e0a\u4e0b\u6587\uff1a"]
        patient_name = context.get("patient_name") or ""
        bed = context.get("bed") or ""
        ward = context.get("ward") or ""
        if patient_name or bed or ward:
            fallback_patient_name = "\u5f53\u524d\u60a3\u8005"
            profile_parts = [
                f"\u59d3\u540d\uff1a{patient_name or fallback_patient_name}",
                f"\u5e8a\u53f7\uff1a{bed or '-'}",
                f"\u75c5\u533a\uff1a{ward or '-'}",
            ]
            if context.get("age"):
                profile_parts.append(f"\u5e74\u9f84\uff1a{context.get('age')}\u5c81")
            if context.get("gender"):
                profile_parts.append(f"\u6027\u522b\uff1a{context.get('gender')}")
            if context.get("height"):
                profile_parts.append(f"\u8eab\u9ad8\uff1a{context.get('height')}")
            if context.get("weight"):
                profile_parts.append(f"\u4f53\u91cd\uff1a{context.get('weight')}")
            lines.append("\uff1b".join(profile_parts) + "\u3002")
        if context.get("diagnosis"):
            lines.append(f"\u8bca\u65ad/\u4e3b\u8bc9\uff1a{context.get('diagnosis')}")
        if context.get("allergies"):
            lines.append(f"\u8fc7\u654f\u53f2\uff1a{context.get('allergies')}")
        if context.get("contraindications"):
            lines.append(f"\u7981\u5fcc\u6216\u98ce\u9669\uff1a{context.get('contraindications')}")
        if context.get("nursing_note"):
            lines.append(f"\u62a4\u7406\u63d0\u9192\uff1a{context.get('nursing_note')}")
        if context.get("prescription_note"):
            lines.append(f"\u533b\u5631\u6458\u8981\uff1a{context.get('prescription_note')}")
        drugs = context.get("drugs") or []
        if drugs:
            lines.append("\u672c\u6b21\u914d\u9001\u836f\u54c1\uff1a")
            for index, drug in enumerate(drugs[:8], start=1):
                if not isinstance(drug, dict):
                    continue
                parts = [str(drug.get("drug_name") or "\u672a\u547d\u540d\u836f\u54c1")]
                for key, label in (
                    ("dose", "\u5242\u91cf"),
                    ("frequency", "\u9891\u6b21"),
                    ("route_label", "\u9014\u5f84"),
                    ("timing", "\u65f6\u673a"),
                    ("duration", "\u7597\u7a0b"),
                    ("precautions", "\u6ce8\u610f"),
                    ("doctor_note", "\u5907\u6ce8"),
                    ("usage_text", "\u8bf4\u660e"),
                ):
                    value = str(drug.get(key) or "").strip()
                    if value:
                        parts.append(f"{label}:{value}")
                lines.append(f"{index}. " + "\uff1b".join(parts))
        lines.append(
            "\u56de\u7b54\u65f6\u4f18\u5148\u4f7f\u7528\u4e0a\u9762\u8fd9\u4e2a\u75c5\u4eba\u5f53\u524d\u914d\u9001\u4efb\u52a1\u4e2d\u7684\u836f\u54c1\u548c\u533b\u5631\u3002"
            "\u5982\u679c\u7528\u6237\u95ee\u5177\u4f53\u836f\u600e\u4e48\u5403\uff0c\u53ea\u80fd\u4f9d\u636e\u4e0a\u4e0b\u6587\u5df2\u6709\u7684\u5242\u91cf\u3001\u9891\u6b21\u3001\u9014\u5f84\u548c\u6ce8\u610f\u4e8b\u9879\u56de\u7b54\u3002"
            "\u5982\u679c\u4e0a\u4e0b\u6587\u6ca1\u5199\u660e\u5242\u91cf\u6216\u996d\u524d\u996d\u540e\uff0c\u4e0d\u8981\u731c\uff0c\u8981\u8bf4\u6211\u8fd9\u8fb9\u6682\u65f6\u6ca1\u770b\u5230\u660e\u786e\u8bb0\u5f55\uff0c\u8bf7\u6309\u533b\u5631\u6216\u95ee\u62a4\u58eb\u3002"
            "\u4e0d\u8981\u4e3b\u52a8\u4f7f\u7528\u6444\u50cf\u5934\u8bc6\u522b\u5230\u7684\u836f\u54c1\u4ee3\u66ff\u672c\u6b21\u914d\u9001\u4efb\u52a1\u7684\u836f\u54c1\u3002"
        )
        return "\n".join(lines) + "\n\n"

    def clean_text(self, value):
        text = str(value or "").strip()
        if len(text) > self.max_input_chars:
            text = text[: self.max_input_chars]
        return text

    def extract_chat_content(self, value):
        raw = str(value or "").strip()
        if not raw:
            return ""
        try:
            payload = json.loads(raw)
            if isinstance(payload, dict):
                return self.clean_text(payload.get("content") or payload.get("text") or payload.get("message"))
        except json.JSONDecodeError:
            pass
        return self.clean_text(raw)

    def normalize_echo_text(self, text):
        normalized = str(text or "").lower()
        normalized = re.sub(r"[\s\W_]+", "", normalized, flags=re.UNICODE)
        return normalized

    def is_echo_of_recent_answer(self, text):
        candidate = self.normalize_echo_text(text)
        if len(candidate) < 4:
            return False
        now = time.monotonic()
        active_answers = []
        for item in self.recent_answers[-6:]:
            if now - item.get("time", 0.0) <= self.echo_filter_window_sec:
                active_answers.append(item)
        self.recent_answers = active_answers
        for item in active_answers:
            reference = item.get("normalized", "")
            if not reference:
                continue
            if candidate in reference or reference in candidate:
                return True
            if SequenceMatcher(None, candidate, reference).ratio() >= self.echo_similarity_threshold:
                return True
        return False

    def remember_answer_for_echo_filter(self, answer):
        normalized = self.normalize_echo_text(answer)
        now = time.monotonic()
        self.last_answer_time = now
        if len(normalized) < 4:
            return
        self.recent_answers.append({"normalized": normalized, "time": now})
        self.recent_answers = self.recent_answers[-6:]

    def is_meaningful_mic_input(self, text):
        cleaned = str(text or "").strip()
        normalized = self.normalize_echo_text(cleaned)
        short_intent_terms = (
            "\u8c01", "\u5417", "\u5462", "\u54ea", "\u54ea\u4e9b", "\u6709\u6ca1\u6709",
            "\u8fd8\u6709", "\u8fd9\u4e2a", "\u90a3\u4e2a", "\u7ee7\u7eed", "\u518d\u8bf4",
            "\u91cd\u8bf4", "\u91cd\u590d", "\u518d\u6765\u4e00\u6b21", "\u7ee7\u7eed\u8bb2",
            "\u8fd9\u4e2a", "\u90a3\u4e2a", "\u75bc", "\u75db", "\u53ef\u4ee5", "\u597d", "\u606d\u559c",
        )
        has_question_mark = cleaned.endswith(("\uff1f", "?"))
        has_short_intent = has_question_mark or any(term in cleaned for term in short_intent_terms)
        if len(normalized) < 3 and not has_short_intent:
            return False
        # Obvious ASR fragments/noise seen on the board. Keep strings ASCII-escaped to avoid deployment mojibake.
        noise_terms = ("\u6cd5\u5f8b\u6216", "\u5b57\u5e55", "\u8c22\u8c22\u89c2\u770b", "\u55ef\u55ef", "\u554a\u554a", "\u5443\u5443", "\u624d\u5e38\u597d\u5403\u8fd9\u4e2a\u836f", "\u597d\u5403")
        if any(term in cleaned for term in noise_terms):
            return False
        question_terms = ("\u5417", "\u5462", "\u4ec0\u4e48", "\u600e\u4e48", "\u4e3a\u4f55", "\u4e3a\u4ec0\u4e48", "\u80fd\u4e0d\u80fd", "\u53ef\u4e0d\u53ef\u4ee5", "\u662f\u4e0d\u662f", "\u8c01", "\u54ea\u91cc", "\u54ea\u4e9b", "\u6709\u54ea\u4e9b", "\u6709\u6ca1\u6709", "\u8fd8\u6709", "\u591a\u5c11", "\u591a\u4e45", "\u51e0", "\u5982\u4f55", "\u8bf7\u95ee", "\u5e2e\u6211", "\u544a\u8bc9\u6211", "\u6f0f\u670d", "\u526f\u4f5c\u7528", "\u8fc7\u654f", "\u559d\u9152", "\u7981\u5fcc", "\u6ce8\u610f", "\u7528\u6cd5", "\u7528\u91cf", "\u996d\u524d", "\u996d\u540e", "\u4ec0\u4e48\u65f6\u5019\u5403", "\u5403\u51e0", "\u5403\u591a\u5c11", "\u4e0d\u8212\u670d", "\u5934\u6655", "\u6076\u5fc3", "\u53d1\u70e7", "\u8840\u538b", "\u75bc", "\u75db", "\u8fd9\u4e2a", "\u90a3\u4e2a", "\u8fd9\u4e2a\u836f", "\u8fd9\u836f", "\u836f\u600e\u4e48", "\u7ee7\u7eed", "\u518d\u8bf4", "\u91cd\u8bf4", "\u91cd\u590d", "\u518d\u6765\u4e00\u6b21", "\u4e3a\u4ec0\u4e48\u8fd8", "\u4e3a\u4ec0\u4e48\u6ca1", "\u600e\u4e48\u529e")
        has_intent = has_question_mark or any(term in cleaned for term in question_terms)
        if not has_intent and ("\u836f" in cleaned) and any(term in cleaned for term in ("\u5403", "\u7528", "\u559d", "\u6ce8\u610f", "\u7981\u5fcc", "\u7528\u6cd5", "\u7528\u91cf")):
            has_intent = True
        # Very short fragments after AI finished speaking are usually TTS tail/noise.
        if time.monotonic() - self.last_answer_time <= self.mic_post_answer_guard_sec:
            if len(normalized) < 10 and not has_intent:
                return False
        if not self.mic_require_intent:
            return True
        if has_intent:
            return True
        # Declarative short fragments after playback should not wake the model.
        return False

    def is_wake_word_only(self, text):
        normalized = self.normalize_echo_text(text)
        return normalized in {"\u673a\u5668\u4eba", "\u673a\u5668", "\u5c0f\u836f\u52a9", "\u836f\u52a9", "\u5c0f\u52a9\u624b"}

    def enqueue_chat(self, text, source):
        now = time.monotonic()
        if source == "mic" and not self.is_meaningful_mic_input(text):
            if self.respond_to_wake_word_only and self.is_wake_word_only(text):
                self.publish_response(text, "\u6211\u5728\uff0c\u60a8\u6162\u6162\u8bf4\u3002", source, ok=True, knowledge_matches=[])
                self.get_logger().info(f"Wake-word-only mic input acknowledged: {text}")
            else:
                self.get_logger().info(f"Ignored low-intent mic input: {text}")
            return
        if self.is_echo_of_recent_answer(text):
            self.get_logger().info(f"Ignored probable AI self-echo from {source}: {text}")
            return
        if source == "mic":
            normalized_question = self.normalize_echo_text(text)
            if normalized_question:
                last_seen = self.recent_mic_questions.get(normalized_question, 0.0)
                if now - last_seen <= self.mic_repeat_suppress_sec:
                    self.get_logger().info(f"Ignored repeated mic question within suppress window: {text}")
                    return
                self.recent_mic_questions[normalized_question] = now
                cutoff = now - max(30.0, self.mic_repeat_suppress_sec)
                self.recent_mic_questions = {
                    key: ts for key, ts in self.recent_mic_questions.items() if ts >= cutoff
                }
        if text == self.last_text and now - self.last_time < self.deduplicate_window_sec:
            return
        self.last_text = text
        self.last_time = now
        item = {"text": text, "source": source, "time": time.time()}
        if self.pending.full():
            try:
                self.pending.get_nowait()
                self.pending.task_done()
            except queue.Empty:
                pass
        self.pending.put(item)
        self.get_logger().info(f"AI chat queued from {source}: {text}")

    def chat_worker(self):
        while self.running:
            try:
                item = self.pending.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                self.handle_chat(item)
            except Exception as exc:
                self.get_logger().warn(f"AI chat failed: {exc}")
                self.publish_response(
                    item["text"],
                    f"大模型暂时没有响应：{exc}",
                    item["source"],
                    ok=False,
                )
            finally:
                self.pending.task_done()

    def handle_chat(self, item):
        question = item["text"]
        patient_context_prompt = self.build_patient_context_prompt()
        knowledge_query = f"{question} {patient_context_prompt}" if patient_context_prompt else question
        allow_vision_context = (not patient_context_prompt) or self.use_vision_context_when_patient_context_active
        if allow_vision_context and self.latest_vision_context and time.time() - self.latest_vision_context_at <= 300:
            knowledge_query = f"{knowledge_query} {self.latest_vision_context}"
        knowledge_matches = self.search_knowledge(knowledge_query)
        messages = self.build_chat_messages(
            question,
            knowledge_matches,
            patient_context_prompt=patient_context_prompt,
        )
        answer = self.call_chat_completion(messages)
        answer = self.clean_answer(answer)
        if answer:
            self.history.append({"role": "user", "content": question})
            self.history.append({"role": "assistant", "content": answer})
            self.history = self.trim_history(self.history)
            self.publish_response(question, answer, item["source"], ok=True, knowledge_matches=knowledge_matches)

    def build_chat_messages(self, question, knowledge_matches, patient_context_prompt=""):
        history = self.trim_history(self.history)
        vision_context = ""
        identity_instruction = ""
        if any(term in str(question or "") for term in ("你是谁", "你叫什么", "机器人你是谁", "介绍一下你自己")):
            identity_instruction = (
                "用户只是问你是谁时，只简短介绍自己的名字和能做什么，"
                "不要主动展开药品清单、用法用量或服用注意事项，除非用户继续追问药品。\n"
            )
        allow_vision_context = (not patient_context_prompt) or self.use_vision_context_when_patient_context_active
        if allow_vision_context and self.latest_vision_context and time.time() - self.latest_vision_context_at <= 300:
            vision_context = (
                "当前摄像头上下文："
                f"{self.latest_vision_context}\n"
                "仅在没有当前病人配送任务上下文时，才把这里作为药品参考。\n\n"
            )
        if not knowledge_matches:
            user_content = patient_context_prompt + vision_context + identity_instruction + (
                "用户的问题没有命中本地知识库。请像医院床旁语音助手一样自然回答，"
                "但不能承诺摆药、倒水、准备温水、扶人、喂药、替患者服药、亲自联系护士等机器人做不到的动作。"
                "不要反复说“资料中没有找到”或“资料中没有明确说明”；"
                "可以换成“我这边暂时没看到明确记录”。"
                "如果是健康、药品或疾病问题，可以给通用科普和就医提醒；"
                "如果不是医疗问题，就简短说明自己主要负责配送和健康科普。"
                "如果用户询问天气、新闻、价格、实时状态等需要联网实时查询的信息，"
                "要自然说明当前不能查询实时信息，不要猜测或编造。"
                "不要诊断疾病，不要编造药品剂量，不要建议自行停药、换药或调整处方。"
                "如果上下文只有“降压药、退烧药、止痛药”这类泛称，不要判断饭前饭后、早晚或一次几片。"
                "避免列表式、说明书式口吻；优先用两三句口语化短句回答。\n\n"
                f"用户问题：{question}"
            )
            return history + [{"role": "user", "content": user_content}]

        context_lines = []
        used_chars = 0
        for index, match in enumerate(knowledge_matches, start=1):
            text = match["text"].strip()
            remaining = self.knowledge_max_chars - used_chars
            if remaining <= 0:
                break
            if len(text) > remaining:
                text = text[:remaining].rstrip()
            used_chars += len(text)
            context_lines.append(
                f"[资料{index}] {match['title']} ({match['source']})\n{text}"
            )
        knowledge_block = "\n\n".join(context_lines)
        user_content = patient_context_prompt + vision_context + identity_instruction + (
            "请优先根据下面的院内轻量知识库资料回答。"
            "资料只作为参考，不要机械复述资料标题或来源。"
            "如果资料只部分相关，请自然说明通用注意事项，不要反复说“资料中没有找到”。"
            "语气要像床旁语音助手在提醒老人：亲切、简短、不要吓人。"
            "但不能承诺摆药、倒水、准备温水、扶人、喂药、替患者服药、亲自联系护士等机器人做不到的动作。"
            "如果和上一轮意思相近，请换一种更短更自然的说法，不要逐字重复。"
            "如果资料或病人上下文没有给出明确用法，不要推测饭前饭后、早晚或剂量。"
            "如果用户问漏服，且涉及降糖药、胰岛素、抗凝药、心脏药、抗癫痫药等高风险药，"
            "不要给具体补服或跳过方案；只提醒不要补双倍，并请护士、医生或药师确认。"
            "不要编造剂量、诊断或治疗方案。\n\n"
            f"用户问题：{question}\n\n"
            f"知识库资料：\n{knowledge_block}"
        )
        self.get_logger().info(
            "Knowledge matches: "
            + "; ".join(f"{m['title']} score={m['score']:.1f}" for m in knowledge_matches)
        )
        return history + [{"role": "user", "content": user_content}]

    def trim_history(self, history):
        if self.history_length <= 0:
            return history[-1:]
        system = history[:1] if history and history[0].get("role") == "system" else []
        rest = history[1:] if system else history
        return system + rest[-self.history_length:]

    def call_chat_completion(self, messages):
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.use_model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {self.api_key}",
        }
        request = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_sec) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {detail[:160]}") from exc
        payload = json.loads(body)
        choices = payload.get("choices") or []
        if not choices:
            raise RuntimeError("empty model response")
        message = choices[0].get("message") or {}
        return str(message.get("content") or "").strip()

    def clean_answer(self, answer):
        text = str(answer or "").strip()
        if self.strip_think_tags:
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()
        # TTS-safe cleanup: remove Markdown and symbols that speech engines read aloud.
        text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
        text = re.sub(r"`([^`]*)`", r"\1", text)
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"__([^_]+)__", r"\1", text)
        text = re.sub(r"[*_#>`~]+", " ", text)
        text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", text)
        text = text.replace("\u2014\u2014", "\uff0c").replace("\u2013", "\uff0c").replace("--", "\uff0c")
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        text = self.humanize_answer_text(text)
        text = self.compress_spoken_answer(text)
        text = self.capability_boundary_guard(text)
        text = self.high_risk_missed_dose_guard(text)
        text = self.smart_truncate_for_tts(text, self.max_reply_chars)
        return text

    def compress_spoken_answer(self, text):
        """Make spoken answers shorter and less repetitive without losing the main point."""
        cleaned = str(text or "").strip()
        if not cleaned:
            return ""
        sentences = [s.strip() for s in re.split(r"(?<=[。！？])\s*", cleaned) if s.strip()]
        if not sentences:
            return cleaned

        picked = []
        seen = set()
        for sentence in sentences:
            if sentence in seen:
                continue
            seen.add(sentence)
            picked.append(sentence)
            if len(picked) >= 3:
                break

        merged = "".join(picked) if picked else cleaned

        # If the answer is still long, keep only the first two spoken sentences.
        if len(merged) > 120 and len(picked) > 2:
            merged = "".join(picked[:2])

        merged = re.sub(r"([。！？])\1+", r"\1", merged)
        return merged.strip()

    def smart_truncate_for_tts(self, text, max_chars):
        """Keep TTS answers short without cutting off in the middle of a sentence."""
        text = str(text or "").strip()
        if not text or max_chars <= 0 or len(text) <= max_chars:
            return text
        head = text[:max_chars].rstrip()
        # Prefer a complete Chinese/English sentence boundary near the end.
        best = -1
        for mark in ("。", "！", "？", ".", "!", "?", "；", ";"):
            pos = head.rfind(mark)
            if pos > best:
                best = pos
        min_keep = max(60, int(max_chars * 0.55))
        if best >= min_keep:
            return head[: best + 1].rstrip()
        # Otherwise cut at a soft phrase boundary and add a natural closing phrase.
        best = -1
        for mark in ("，", ",", "、", " "):
            pos = head.rfind(mark)
            if pos > best:
                best = pos
        if best >= min_keep:
            head = head[:best].rstrip(" ，,、")
        else:
            head = head.rstrip(" ，,、；;")
        if not head.endswith(("。", "！", "？", ".", "!", "?")):
            head += "。"
        return head

    def humanize_answer_text(self, text):
        """Light post-processing for TTS: avoid robotic disclaimers and repeated KB misses."""
        cleaned = str(text or "").strip()
        if not cleaned:
            return ""
        replacements = (
            ("资料中没有找到", "我这边暂时没看到明确记录"),
            ("资料中没有明确说明", "我这边暂时没看到明确说明"),
            ("根据资料显示，", ""),
            ("根据提供的资料，", ""),
            ("根据院内轻量知识库资料，", ""),
            ("作为医院配送机器人，", ""),
            ("我是医院配送机器人，", "我主要负责送药和用药提醒，"),
            ("饭前饭后都可以", "饭前还是饭后要按药盒或医嘱来"),
            ("多数是早上服用，", ""),
            ("多数是早上服用", ""),
            ("多数人适合早晨吃，", ""),
            ("多数人适合早晨吃", ""),
            ("多数是早晨服用，", ""),
            ("多数是早晨服用", ""),
        )
        for old, new in replacements:
            cleaned = cleaned.replace(old, new)
        # Keep the safety reminder, but avoid repeating it many times in one short spoken answer.
        consult_patterns = (
            "请咨询医生或护士",
            "请联系医生或护士",
            "请咨询医生、护士或药师",
            "请联系医生、护士或药师",
        )
        first_seen = None
        for pattern in consult_patterns:
            if pattern in cleaned:
                first_seen = pattern
                break
        if first_seen:
            for pattern in consult_patterns:
                if pattern == first_seen:
                    continue
                cleaned = cleaned.replace(pattern, first_seen)
            parts = cleaned.split(first_seen)
            if len(parts) > 2:
                cleaned = first_seen.join(parts[:2]) + "".join(parts[2:])
        cleaned = re.sub(r"(请先核对身份和药品[。！？，, ]*){2,}", "请先核对身份和药品。", cleaned)
        cleaned = re.sub(r"(我可以继续播报用药说明[。！？，, ]*){2,}", "我可以继续播报用药说明。", cleaned)
        cleaned = re.sub(r"^(好的[，。]\s*){2,}", "好的，", cleaned)
        cleaned = re.sub(r"([。！？])\1+", r"\1", cleaned)
        return cleaned.strip()

    def high_risk_missed_dose_guard(self, text):
        """Avoid giving concrete missed-dose instructions for high-risk medicines."""
        cleaned = str(text or "").strip()
        if not cleaned:
            return ""
        high_risk_terms = (
            "抗凝", "华法林", "阿司匹林", "胰岛素", "降糖", "降压", "心衰",
            "抗心律失常", "镇静", "安眠", "抗癫痫", "免疫抑制", "化疗",
        )
        missed_terms = ("漏服", "忘服", "忘记吃", "错过", "补服", "少吃", "没吃")
        concrete_terms = ("几小时", "几个小时", "立刻", "马上", "补一片", "补一粒", "补一袋", "双倍", "加倍", "按原剂量", "下一次")
        if any(term in cleaned for term in high_risk_terms) and any(term in cleaned for term in missed_terms):
            return (
                "这类药物漏服后不要自行按固定方案补。"
                "请先看药盒或医嘱，再联系护士、医生或药师确认。"
                "如果已经出现胸痛、低血糖、出血或意识不清，请立刻呼叫医护。"
            )
        if any(term in cleaned for term in concrete_terms) and any(term in cleaned for term in missed_terms):
            return (
                "先不要自行补服或加倍。"
                "请按药盒说明或联系护士、医生、药师确认后再处理。"
            )
        return cleaned

    def capability_boundary_guard(self, text):
        """Prevent the voice assistant from promising physical nursing actions."""
        cleaned = str(text or "").strip()
        if not cleaned:
            return ""
        forbidden_patterns = (
            r"我(?:会|来|可以|帮你|帮您).{0,8}(?:摆|放|备好).{0,8}药",
            r"(?:帮你|帮您|为你|为您).{0,8}(?:摆|放|备好).{0,8}药",
            r"我(?:会|来|可以|帮你|帮您).{0,8}(?:倒|准备|备好|端).{0,8}(?:水|温水|热水)",
            r"(?:帮你|帮您|为你|为您).{0,8}(?:倒|准备|备好|端).{0,8}(?:水|温水|热水)",
            r"我(?:会|来|可以|帮你|帮您).{0,8}(?:扶|搀扶)",
            r"我(?:会|来|可以|帮你|帮您).{0,8}(?:喂药|喂你|喂您)",
            r"我(?:会|来|可以|帮你|帮您).{0,8}(?:联系|通知|叫).{0,8}(?:护士|医生|药师)",
        )
        if any(re.search(pattern, cleaned) for pattern in forbidden_patterns):
            return (
                "我不能直接摆药、倒水、扶您或替您联系护士。"
                "请先核对身份和药品；需要水或身体协助时，请按呼叫铃或请护士、家属帮忙。"
                "我可以继续播报用药说明。"
            )
        return cleaned

    def load_knowledge_base(self):
        root = Path(self.knowledge_dir)
        if not root.exists():
            self.get_logger().warn(f"Knowledge directory not found: {self.knowledge_dir}")
            return
        supported = {".txt", ".md", ".csv", ".json"}
        chunks = []
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in supported:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception as exc:
                self.get_logger().warn(f"Failed to read knowledge file {path}: {exc}")
                continue
            chunks.extend(self.split_knowledge_file(path, text))
        self.knowledge_chunks = chunks
        self.get_logger().info(f"Loaded knowledge base: {len(chunks)} chunks from {self.knowledge_dir}")

    def split_knowledge_file(self, path, text):
        if path.suffix.lower() == ".json":
            text = self.flatten_json_text(text)
        title = path.stem
        parts = re.split(r"\n\s*\n|(?=^#{1,3}\s+)", text, flags=re.MULTILINE)
        chunks = []
        for part in parts:
            cleaned = re.sub(r"\s+", " ", part).strip()
            if len(cleaned) < 20:
                continue
            heading = title
            heading_match = re.match(r"^#{1,3}\s*(.+?)(?:\s|$)", part.strip())
            if heading_match:
                heading = heading_match.group(1).strip()[:60] or title
            chunks.append({
                "title": heading,
                "source": str(path.relative_to(Path(self.knowledge_dir))),
                "text": cleaned[:900],
                "tokens": self.knowledge_tokens(cleaned + " " + heading),
            })
        return chunks

    def flatten_json_text(self, text):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return text
        parts = []

        def walk(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    parts.append(str(key))
                    walk(item)
            elif isinstance(value, list):
                for item in value:
                    walk(item)
            else:
                parts.append(str(value))

        walk(payload)
        return "\n".join(parts)

    def knowledge_tokens(self, text):
        normalized = str(text or "").lower()
        tokens = set(re.findall(r"[a-z0-9]+", normalized))
        important_terms = [
            "老人", "老年", "高龄", "跌倒", "头晕", "降压", "降糖", "血糖", "血压", "抗凝",
            "阿司匹林", "华法林", "胰岛素", "二甲双胍", "感冒", "发热", "咳嗽", "腹泻",
            "漏服", "副作用", "过敏", "胸痛", "呼吸困难", "意识不清", "大出血", "孕妇",
            "怀孕", "儿童", "小孩", "剂量", "退烧", "抗生素", "止痛", "慢病", "复诊",
            "冠心病", "脑梗", "卒中", "肾病", "便秘", "失眠", "安眠药", "镇静", "利尿",
            "黑便", "血尿", "鼻出血", "牙龈", "低血糖", "高血压", "糖尿病", "发烧",
            "退热", "止咳", "哺乳", "备孕", "妊娠", "处方", "药师", "医生", "护士",
        ]
        for term in important_terms:
            if term in normalized:
                tokens.add(term)
        return tokens

    def search_knowledge(self, question):
        if not self.enable_knowledge_base or not self.knowledge_chunks:
            return []
        query_tokens = self.knowledge_tokens(question)
        if not query_tokens:
            return []
        scored = []
        question_text = str(question or "")
        for chunk in self.knowledge_chunks:
            overlap = query_tokens & chunk["tokens"]
            if not overlap:
                continue
            score = float(len(overlap))
            if any(term in question_text for term in ("老人", "老年", "高龄", "爸", "妈", "爷爷", "奶奶", "外公", "外婆")):
                if any(term in chunk["text"] for term in ("老人", "老年", "高龄")):
                    score += 3.0
            if any(term in question_text for term in ("儿童", "小孩", "孩子", "宝宝")):
                if any(term in chunk["text"] for term in ("儿童", "小孩", "孩子")):
                    score += 2.0
            if any(term in question_text for term in ("孕妇", "怀孕", "妊娠")):
                if any(term in chunk["text"] for term in ("孕妇", "怀孕", "妊娠")):
                    score += 2.0
            if score >= self.knowledge_min_score:
                scored.append({**chunk, "score": score})
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[: max(1, self.knowledge_max_chunks)]

    def publish_response(self, question, answer, source, ok=True, knowledge_matches=None):
        data = {
            "ok": ok,
            "source": source,
            "question": question,
            "answer": answer,
            "model": self.use_model,
            "knowledge_sources": [
                {"title": item["title"], "source": item["source"], "score": item["score"]}
                for item in (knowledge_matches or [])
            ],
            "stamp": time.time(),
        }
        msg = String()
        msg.data = json.dumps(data, ensure_ascii=False)
        self.ai_response_pub.publish(msg)

        chat_msg = String()
        chat_msg.data = json.dumps(
            {"content": answer, "model": self.use_model, "is_done": True, "ok": ok},
            ensure_ascii=False,
        )
        self.chat_response_pub.publish(chat_msg)

        if self.publish_voice and answer:
            self.remember_answer_for_echo_filter(answer)
            voice_msg = String()
            voice_msg.data = f"{self.voice_prefix}{answer}"
            self.voice_pub.publish(voice_msg)
        self.get_logger().info(f"AI chat response published: {answer}")

    def destroy_node(self):
        self.running = False
        if self.worker.is_alive():
            self.worker.join(timeout=1.0)
        super().destroy_node()


def main():
    rclpy.init()
    node = AiVoiceChatBridgeNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
