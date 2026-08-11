Getting started
---------------

This server doesn't require installation, all of its files are self-contained.
Just download the latest server files from the `project
releases page <https://github.com/csev1755/rokenbok-webserver/releases/latest>`_ 
and extract it to a folder of your choice. Keep in mind the executable and
``settings.ini`` need to stay together in the same folder for the server to
read its configuration.

Configuration
~~~~~~~~~~~~~

The ``settings.ini`` file holds all the options for the server and can be edited
with any plain text editor (such as Notepad on Windows or TextEdit on macOS).
Settings are grouped into sections marked with square brackets (like
``[webserver]``), and each setting follows a ``name = value`` format. To
change a setting, just edit the value after the ``=`` sign.
Anything starting with ``#`` are comments and are ignored by the server.

To change any settings, stop the server if it's running,
edit the ``settings.ini`` file, and then run the server again.

Webserver
^^^^^^^^^^

These are the main configuration settings for the server:

.. code-block:: ini

   [webserver]
   listen_ip = 0.0.0.0
   listen_port = 5001
   enable_video = false
   player_timeout = 30

Generally, you shouldn't need to change the ``listen_ip`` or ``listen_port`` unless you have a specific reason to do so. 
The ``enable_video`` option can be set to ``true`` if you want to enable the video stream feature, and ``player_timeout`` 
sets the number of seconds a player can be idle before their vehicle selection is released for others to use.

Devices
^^^^^^^

Each supported vehicle control device has its own named sections.
Details for these options are documented in :doc:`devices`.

.. code-block:: ini

   [device]
   # Device-specific settings

   [device.vehicles]
   1 = Vehicle One
   2 = Vehicle Two

Video streams
^^^^^^^^^^^^^

To enable the video stream, set ``enable_video`` to ``true`` in the ``[webserver]`` section 
and start the server once to see which video devices were detected:

.. code-block::

   * Found go2rtc video device 0 - Generic Webcam - ffmpeg:device?video=0#video=h264
   * Found go2rtc video device 1 - USB Camera - ffmpeg:device?video=1#video=h264

Copy the text after the device name (starting with ``ffmpeg:``) into
the ``[video_streams]`` section for each camera you want to use along with
a name that will be shown in the web interface. For example:

.. code-block:: ini

   [video_streams]
   Camera 1 = ffmpeg:device?video=0#video=h264
   Camera 2 = ffmpeg:device?video=1#video=h264

Updating
~~~~~~~~

To update the server, you should only have to replace the executable.
