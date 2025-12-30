# Kindle Photo Frame Server

A simple web server that lets you upload, crop (3:4 aspect ratio), rotate, and convert images to 8-bit grayscale for display on a Kindle e-ink screen.

## Features

- **Image Upload**: Upload images from your device (PNG, JPG, GIF, BMP, WebP)
- **3:4 Crop**: Interactive cropping with locked 3:4 aspect ratio (ideal for Kindle portrait mode)
- **Rotation**: Rotate images in 90° increments
- **Grayscale Conversion**: Automatically converts to 8-bit grayscale PNG for Kindle e-ink display
- **Live Preview**: See the final grayscale result before applying

## Installation

1. Clone or copy this project to your Raspberry Pi

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server:
```bash
python server.py
```

The server will start on `http://0.0.0.0:8088`

## Usage

1. Open `http://YOUR_RPI_IP:8088` in a browser
2. Upload an image
3. Adjust the crop area (locked to 3:4 ratio)
4. Rotate if needed
5. Click "Apply & Preview" to see the grayscale result
6. The processed image is now available at `http://YOUR_RPI_IP:8088/frame.png`

## Kindle Setup

Configure your Kindle's `env.sh` to fetch from:
```
http://YOUR_RPI_IP:8088/frame.png
```

## Running as a Service (Optional)

To run the server automatically on boot, create a systemd service:

```bash
sudo nano /etc/systemd/system/kindle-frame.service
```

```ini
[Unit]
Description=Kindle Photo Frame Server
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/server.py
WorkingDirectory=/path/to/kindle-photo-frame
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Then enable and start:
```bash
sudo systemctl enable kindle-frame
sudo systemctl start kindle-frame
```

## File Structure

```
kindle-photo-frame/
├── server.py           # Flask server
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html      # Web dashboard
├── uploads/            # Uploaded images (auto-created)
└── output/             # Processed images (auto-created)
    └── frame.png       # Current frame for Kindle
```
