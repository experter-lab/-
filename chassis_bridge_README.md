# medicine_chassis_bridge

ROS 2 chassis bridge for the medicine delivery robot.

## Public ROS interface

- Subscribe: `/cmd_vel` (`geometry_msgs/msg/Twist`)
- Publish: `/odom` (`nav_msgs/msg/Odometry`)
- Publish TF: `odom -> base_link`
- Publish status: `/medicine/chassis_status` (`std_msgs/msg/String`, JSON)
- Service: `/chassis_bridge/set_emergency_stop` (`std_srvs/srv/SetBool`)
- Service: `/chassis_bridge/reset_odom` (`std_srvs/srv/Trigger`)

## Modes

- `mock`: integrates commanded velocity locally and publishes odometry.
- `serial`: reserved for the lower-level chassis controller. By default `serial_enabled` is false for safety.
- `ardupilot`: reserved for the AET-H743 Basic ArduPilot MAVLink chassis controller. The first configurations are read-only and only parse MAVLink heartbeat/status.

## AET-H743 Basic ArduPilot read-only check

- Hardware: AET-H743 Basic, ArduPilot, serial/UART or USB, four-wheel differential chassis, no wheel encoders.
- Serial config: `config/chassis_bridge_ardupilot_serial_readonly.yaml`.
- USB config: `config/chassis_bridge_ardupilot_readonly.yaml`.
- Recommended serial default: `/dev/ttyUSB1` at `115200`, because `/dev/ttyUSB0` may already be used by the lidar.
- Default safety state:
  - `publish_odom: false` and `publish_tf: false`, so it will not conflict with `rf2o_laser_odometry`.
  - `emergency_stop: true`.
  - `ardupilot_readonly: true`.
  - `ardupilot_control_enabled: false`.
- Status: `/medicine/chassis_status` includes an `ardupilot` JSON object with heartbeat, system id, component id, MAVLink version, vehicle type, autopilot type, base mode, custom mode, and system status.
- Before motor tests, confirm the serial path, ArduPilot vehicle type, Rover/skid-steer output mapping, arming/mode behavior, timeout stop, and physical emergency stop.

## Lower-level MCU protocol placeholder

The future MCU protocol should provide these functions:

- Command from RK3588 to MCU:
  - target linear velocity `v_x` in m/s
  - target angular velocity `w_z` in rad/s
  - emergency stop flag
  - optional checksum / sequence number
- Feedback from MCU to RK3588:
  - measured linear velocity `v_x` in m/s
  - measured angular velocity `w_z` in rad/s
  - optional pose or wheel encoder ticks
  - battery / fault / emergency status
  - checksum / sequence number

Before enabling hardware motion, verify speed limits, timeout stop, emergency stop, and wheel direction on blocks.
