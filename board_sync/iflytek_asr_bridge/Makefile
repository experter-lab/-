CXX ?= g++
CC ?= gcc

ROS_PREFIX ?= /opt/ros/humble
SDK_DIR ?= /mnt/sdcard/iflytek_tts_df41b4a2
MSC_LIB_DIR ?= $(SDK_DIR)/libs/arm64

TARGET = iflytek_asr_bridge

CFLAGS += -g -Wall -I. -I$(SDK_DIR)/include
CXXFLAGS += -g -Wall -std=c++17 -I. -I$(SDK_DIR)/include -I$(ROS_PREFIX)/include
CXXFLAGS += $(shell pkg-config --cflags rclcpp std_msgs 2>/dev/null)

LDFLAGS += -L$(MSC_LIB_DIR)
LDLIBS += -lmsc -lasound -lrt -ldl -lpthread
LDLIBS += $(shell pkg-config --libs rclcpp std_msgs 2>/dev/null)

OBJS = iflytek_asr_bridge.o linuxrec.o speech_recognizer.o

$(TARGET): $(OBJS)
	$(CXX) $(OBJS) -o $@ $(LDFLAGS) $(LDLIBS)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(TARGET) $(OBJS)

.PHONY: clean
