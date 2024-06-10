/*
    CombinedController.cs
    This script handles serial port communication for syringe device control in Unity.
    It scans available serial ports, allowing the user to select one through a dropdown menu.
    Once a serial port is selected, the script reads quaternion data and plunger sensor data from th port.
    The quaternion data undergoes axis transformations to fit Unity's coordinate system,
    and is then used to rotate a syringe model accordingly. The plunger sensor data is used to control
    the motion of a plunger within the syringe. 

    Additional functionality includes calibrating the syringe's rotation using the 'Y' and 'U' keys.
    Author: Pi Ko (pk2269@nyu.edu)
*/

using System;
using System.IO.Ports;
using System.Collections.Generic;
using UnityEngine;
using TMPro;

public class CombinedController : MonoBehaviour
{
    // Reference to the TMP_Dropdown component for serial port selection.
    public TMP_Dropdown dropdown;

    // Baud rate for serial communication. Must match the Arduino setup.
    public int baudRate = 115200;

    // Transform of the object to be rotated based on quaternion data.
    public Transform targetObject;

    // GameObject to control the Plunger Z position.
    public GameObject PlungerControl;

    // GameObject to rotate for calibration.
    public GameObject SyringeCallibrator;

    // Speed of rotation per second for calibration.
    public float rotationSpeed = 100f;

    // SerialPort object for handling serial communication.
    private SerialPort serialPort;

    // Populates the dropdown with available serial ports at startup.
    void Start()
    {
        PopulateDropdownWithSerialPorts();
        dropdown.onValueChanged.AddListener(delegate { DropdownValueChanged(dropdown); });
    }

    // Fills the dropdown menu with names of serial ports.
    private void PopulateDropdownWithSerialPorts()
    {
        List<string> options = new List<string> { "Select Syringe" }; // Default option
        options.AddRange(SerialPort.GetPortNames()); // Add serial port names to the dropdown

        if (options.Count == 0)
        {
            options.Add("No Device");
        }

        dropdown.ClearOptions();
        dropdown.AddOptions(options);
    }

    // Handles changes in the dropdown selection.
    private void DropdownValueChanged(TMP_Dropdown change)
    {
        string selectedPort = change.options[change.value].text;

        if (selectedPort == "Select Syringe")
        {
            CloseSerialPort(); // Ensure the port is closed if no valid selection
            return; // Exit the method without doing anything further
        }

        if (selectedPort != "No Device")
        {
            ConnectToSerialPort(selectedPort);
        }
        else
        {
            CloseSerialPort(); // Close port if "No Device" is selected
        }
    }

    // Establishes connection to a specified serial port.
    private void ConnectToSerialPort(string portName)
    {
        CloseSerialPort(); // Ensure that any existing connection is closed

        try
        {
            serialPort = new SerialPort(portName, baudRate);
            serialPort.Open();
            Debug.Log("Serial port opened successfully.");
        }
        catch (Exception e)
        {
            Debug.LogError($"Failed to open serial port: {e.Message}");
        }
    }

    // Closes the serial port if open.
    private void CloseSerialPort()
    {
        if (serialPort != null && serialPort.IsOpen)
        {
            serialPort.Close();
            Debug.Log("Serial port closed.");
        }
    }

    // Update is called once per frame to handle data reading and application.
    void Update()
    {
        if (serialPort != null && serialPort.IsOpen)
        {
            try
            {
                if (serialPort.BytesToRead > 0)
                {
                    string data = serialPort.ReadLine();
                    if (IsValidQuaternionData(data))
                    {
                        ApplyQuaternion(data);
                    }
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"Failed to read from serial port: {e.Message}");
            }
        }

        float rotationAmount = rotationSpeed * Time.deltaTime;
        if (Input.GetKey(KeyCode.U))
        {
            SyringeCallibrator.transform.Rotate(0, -rotationAmount, 0);
        }
        if (Input.GetKey(KeyCode.Y))
        {
            SyringeCallibrator.transform.Rotate(0, rotationAmount, 0);
        }
    }

    // Validates the format of the received data as quaternion.
    bool IsValidQuaternionData(string data)
    {
        return data.StartsWith("Quat W:") && data.Split(',').Length >= 5;
    }

    // Applies quaternion data to rotate the target object and move the plunger.
    void ApplyQuaternion(string data)
    {
        try
        {
            string[] parts = data.Split(',');
            float w = float.Parse(parts[0].Split(':')[1]);
            float x = float.Parse(parts[1].Split(':')[1]);
            float y = float.Parse(parts[2].Split(':')[1]);
            float z = float.Parse(parts[3].Split(':')[1]);
            float plungerValue = float.Parse(parts[4]);

            Quaternion quat = new Quaternion(-x, -z, -y, w);
            targetObject.localRotation = quat;

            float plungerZ = Mathf.Lerp(-0.0532f, 0.0093f, plungerValue);
            PlungerControl.transform.localPosition = new Vector3(
                PlungerControl.transform.localPosition.x,
                PlungerControl.transform.localPosition.y,
                plungerZ
            );
        }
        catch (Exception e)
        {
            Debug.LogError($"Error parsing quaternion data: {e.Message}");
        }
    }

    // Ensures the serial port is closed when the GameObject is destroyed.
    void OnDestroy()
    {
        CloseSerialPort();
    }
}
