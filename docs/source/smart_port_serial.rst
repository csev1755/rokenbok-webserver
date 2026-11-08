Smart Port Serial
===================

Rokenbok vehicles can be controlled via a device connected to the Smart Port on a Command Deck. This allows for up to 15 vehicles to be controlled by up to 12 simultaneous players.

Smart Port Arduino
------------------

An Arduino sketch to control Rokenbok vehicles over the Smart Port via serial USB.

Requirements
~~~~~~~~~~~~

- Arduino IDE (for installation on the Arduino)
- Rokenbok Command Deck (Gen 1)
- 5V logic Arduino with USB-over-serial support (Uno recommended)
- Mini-DIN 6 cable (the Smart Port connector)

Configuration
~~~~~~~~~~~~~

1. Download the ``smart_port_arduino.ino`` sketch from the `Smart-Port-Arduino repository <https://github.com/stepstools/Rokenbok-Smart-Port-Arduino>`_
2. `Install the sketch with Arduino IDE <https://support.arduino.cc/hc/en-us/articles/4733418441116-Upload-a-sketch-in-Arduino-IDE>`_
3. Modify the following in ``settings.ini``:

   - Add the serial device name/path as ``serial_port`` under the ``[smart_port_serial]`` section or leave it as ``auto``:

   .. code-block:: ini

      [smart_port_serial]
      serial_port = auto

   -  Add the name of each of the vehicles connected along with their number under ``[smart_port_serial.vehicles]``:

   .. code-block:: ini

      [smart_port_serial.vehicles]
      1 = Dozer
      2 = Skiptrack
      3 = Loader
      # ... and so on ...

Wiring the Arduino to the Command Deck
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An easy way to get set up is buying a screw terminal HAT or adapter along with a Mini-DIN 6 breakout cable to make a solid connection without any soldering needed as shown below:

.. image:: static/smart_port_arduino.jpg
   :alt: An Arduino connected to the Smart Port
   :width: 75%
   :align: center

Smart Port pinout
+++++++++++++++++

.. grid:: 1 1 2 2

   .. grid-item::
      :child-align: start

      .. list-table::
         :header-rows: 1

         * - Smart Port pin
           - Arduino pin
           - Function
         * - 1
           - 12
           - MISO
         * - 2
           - 13
           - Serial clock
         * - 3
           - \-
           - Frame end
         * - 4
           - 11
           - MOSI
         * - 5
           - GND
           - Ground
         * - 6
           - 8
           - Slave ready
         * - \-
           - 9 \*
           - Slave ready (virtual)
         * - \-
           - 10 \*
           - Slave select
   .. grid-item::
      :child-align: center
      :padding: 5

      .. image:: static/smart_port_pinout.jpg
         :alt: A diagram of the Smart Port pinout
         :width: 100%

\* Pins 9 and 10 are connected to each other instead of the Smart Port. This can be done with a breadboard jumper wire or even a paperclip.

\*\*  Many diagrams will flip the orientation of these pins horizontally. The image above is looking at the face of the port

Smart Port WiFi
----------------

If you have a `Smart Port Wifi <https://github.com/stepstools/Rokenbok-Smart-Port-WiFi>`_ device with version 0.3.0 or higher,
you can connect it through USB to get the same funcitonality as a Smart Port Arduino. There is one more configuration option available:

   .. code-block:: ini

      [smartport_serial]
      enable_wifi = false

Set to ``true`` to keep the WiFi features enabled, even when connected via USB.
