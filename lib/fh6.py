import socket
import struct

DEFAULT_PORT = 7809
DEFAULT_BIND_ADDR = ""
PACKET_SIZE = 324

PACKET_FORMAT = (
    "<"      # little-endian, no padding
    "i"      # IsRaceOn
    "I"      # TimestampMS
    "fff"    # EngineMaxRpm, EngineIdleRpm, CurrentEngineRpm
    "fff"    # AccelerationX, Y, Z
    "fff"    # VelocityX, Y, Z
    "fff"    # AngularVelocityX, Y, Z
    "fff"    # Yaw, Pitch, Roll
    "ffff"   # NormalizedSuspensionTravel FL, FR, RL, RR
    "ffff"   # TireSlipRatio FL, FR, RL, RR
    "ffff"   # WheelRotationSpeed FL, FR, RL, RR
    "iiii"   # WheelOnRumbleStrip FL, FR, RL, RR
    "iiii"   # WheelInPuddle FL, FR, RL, RR
    "ffff"   # SurfaceRumble FL, FR, RL, RR
    "ffff"   # TireSlipAngle FL, FR, RL, RR
    "ffff"   # TireCombinedSlip FL, FR, RL, RR
    "ffff"   # SuspensionTravelMeters FL, FR, RL, RR
    "i"      # CarOrdinal
    "i"      # CarClass
    "i"      # CarPerformanceIndex
    "i"      # DrivetrainType
    "i"      # NumCylinders
    "I"      # CarGroup
    "f"      # SmashableVelDiff
    "f"      # SmashableMass
    "fff"    # PositionX, Y, Z
    "f"      # Speed
    "f"      # Power
    "f"      # Torque
    "ffff"   # TireTemp FL, FR, RL, RR
    "f"      # Boost
    "f"      # Fuel
    "f"      # DistanceTraveled
    "f"      # BestLap
    "f"      # LastLap
    "f"      # CurrentLap
    "f"      # CurrentRaceTime
    "H"      # LapNumber
    "B"      # RacePosition
    "B"      # Accel
    "B"      # Brake
    "B"      # Clutch
    "B"      # HandBrake
    "B"      # Gear
    "b"      # Steer
    "b"      # NormalizedDrivingLine
    "b"      # NormalizedAIBrakeDifference
)

PACKET_FIELDS = (
    "IsRaceOn",
    "TimestampMS",
    "EngineMaxRpm", "EngineIdleRpm", "CurrentEngineRpm",
    "AccelerationX", "AccelerationY", "AccelerationZ",
    "VelocityX", "VelocityY", "VelocityZ",
    "AngularVelocityX", "AngularVelocityY", "AngularVelocityZ",
    "Yaw", "Pitch", "Roll",
    "NormalizedSuspensionTravelFrontLeft", "NormalizedSuspensionTravelFrontRight",
    "NormalizedSuspensionTravelRearLeft", "NormalizedSuspensionTravelRearRight",
    "TireSlipRatioFrontLeft", "TireSlipRatioFrontRight",
    "TireSlipRatioRearLeft", "TireSlipRatioRearRight",
    "WheelRotationSpeedFrontLeft", "WheelRotationSpeedFrontRight",
    "WheelRotationSpeedRearLeft", "WheelRotationSpeedRearRight",
    "WheelOnRumbleStripFrontLeft", "WheelOnRumbleStripFrontRight",
    "WheelOnRumbleStripRearLeft", "WheelOnRumbleStripRearRight",
    "WheelInPuddleFrontLeft", "WheelInPuddleFrontRight",
    "WheelInPuddleRearLeft", "WheelInPuddleRearRight",
    "SurfaceRumbleFrontLeft", "SurfaceRumbleFrontRight",
    "SurfaceRumbleRearLeft", "SurfaceRumbleRearRight",
    "TireSlipAngleFrontLeft", "TireSlipAngleFrontRight",
    "TireSlipAngleRearLeft", "TireSlipAngleRearRight",
    "TireCombinedSlipFrontLeft", "TireCombinedSlipFrontRight",
    "TireCombinedSlipRearLeft", "TireCombinedSlipRearRight",
    "SuspensionTravelMetersFrontLeft", "SuspensionTravelMetersFrontRight",
    "SuspensionTravelMetersRearLeft", "SuspensionTravelMetersRearRight",
    "CarOrdinal", "CarClass", "CarPerformanceIndex", "DrivetrainType", "NumCylinders",
    "CarGroup",
    "SmashableVelDiff", "SmashableMass",
    "PositionX", "PositionY", "PositionZ",
    "Speed", "Power", "Torque",
    "TireTempFrontLeft", "TireTempFrontRight",
    "TireTempRearLeft", "TireTempRearRight",
    "Boost", "Fuel", "DistanceTraveled",
    "BestLap", "LastLap", "CurrentLap",
    "CurrentRaceTime",
    "LapNumber",
    "RacePosition",
    "Accel", "Brake", "Clutch", "HandBrake",
    "Gear",
    "Steer",
    "NormalizedDrivingLine",
    "NormalizedAIBrakeDifference",
)

_STRUCT = struct.Struct(PACKET_FORMAT)


def parse_packet(data):
    return dict(zip(PACKET_FIELDS, _STRUCT.unpack_from(data)))


def listen_raw(port=DEFAULT_PORT, bind_addr=DEFAULT_BIND_ADDR):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((bind_addr, port))
        while True:
            data, _ = sock.recvfrom(PACKET_SIZE)
            yield data


def listen(port=DEFAULT_PORT, bind_addr=DEFAULT_BIND_ADDR):
    for data in listen_raw(port, bind_addr):
        yield parse_packet(data)
