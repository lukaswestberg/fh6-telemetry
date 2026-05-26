import socket
import json
import struct

# Define port
PORT = 7809
BIND_ADDR = ''  # Bind to all interfaces

# Define the packet size (324 bytes)
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

def parse_packet(data):
    values = struct.unpack_from(PACKET_FORMAT, data, 0)
    return dict(zip(PACKET_FIELDS, values))

def main():
    # Start UDP server on port 7809 (bind to all interfaces)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((BIND_ADDR, PORT))
    print("UDP server is listening on port 7809...")
    
    last_packet = None
    while True:
        # Receive data from the client
        data, addr = server_socket.recvfrom(PACKET_SIZE)
        print(f"Received packet from {addr}: {data.hex()}")
        # Parse the packet
        parsed_data = parse_packet(data)
        print(json.dumps(parsed_data, indent=4))
        
        
        

if __name__ == "__main__":
    main()