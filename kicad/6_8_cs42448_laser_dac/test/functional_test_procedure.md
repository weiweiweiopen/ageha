# Functional Test Procedure (Template)

1. Apply power and verify rails.
2. Verify I2C detects CS42448.
3. Stream test TDM audio data from Teensy.
4. Measure all 8 output channels.
5. Confirm DC-coupled amp stage can hit 0V and ±5V setpoints.
