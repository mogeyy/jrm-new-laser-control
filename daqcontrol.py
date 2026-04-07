import nidaqmx

class LaserController:
    def __init__(self, x_channel='Dev1/ao0', y_channel='Dev1/ao1', min_volt=0, max_volt=4):
        """
        Initializes the connection to the NI DAQ.
        
        Args:
            x_channel (str): The name of the DAQ channel for the X-axis mirror.
            y_channel (str): The name of the DAQ channel for the Y-axis mirror.
            min_volt (float): The minimum output voltage.
            max_volt (float): The maximum output voltage.
        """
        # NOTE: You may need to change 'Dev1/ao0' and 'Dev1/ao1' to match
        # your device's name, which you can find in the NI MAX software.
        self.channels = f"{x_channel}, {y_channel}"
        self.min_volt = min_volt
        self.max_volt = max_volt
        
        try:
            self.task = nidaqmx.Task()
            self.task.ao_channels.add_ao_voltage_chan(
                self.channels,
                min_val=self.min_volt,
                max_val=self.max_volt
            )
            print("NI DAQ initialized successfully.")
        except Exception as e:
            print(f"Error initializing DAQ: {e}")
            self.task = None

    def set_position(self, voltage_x, voltage_y):
        """Sends a voltage pair to the DAQ to position the laser."""
        if self.task:
            try:
                # Clamp voltages to be within the safe range
                voltage_x = max(self.min_volt, min(self.max_volt, voltage_x))
                voltage_y = max(self.min_volt, min(self.max_volt, voltage_y))
                
                # Write the two voltage values to the two channels
                self.task.write([voltage_x, voltage_y], auto_start=True)
                print(f"Set laser position to voltages: X={voltage_x:.2f} V, Y={voltage_y:.2f} V")
            except Exception as e:
                print(f"Error writing to DAQ: {e}")

    def close(self):
        """Safely closes the connection to the DAQ."""
        if self.task:
            # Set output to 0V before closing for safety
            self.set_position(0, 0)
            self.task.close()
            print("NI DAQ connection closed.")