# TeleArchiver

A Python script that allows users to download all media files, including PDFs, images, and videos, from a specific Telegram group or channel using the Telethon library. This script utilizes a GUI for ease of use, created with Tkinter. It is designed for both beginner and advanced users who need to efficiently extract media from Telegram.

## Features

- **Download PDFs, Images, Videos**: Automatically downloads all supported file types from a group or channel.
- **Graphical User Interface**: Built using Tkinter, with progress tracking, download logs, and user prompts for API information.
- **Avoid Duplicate Downloads**: Checks if a file already exists before downloading, reducing redundancy.

## Requirements

- Python 3.7+
- Telethon (`pip install telethon`)
- Tkinter (usually included with Python)

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/telearchiver.git
   cd telearchiver
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Script**:
   ```bash
   python telearchiver.py
   ```

## Configuration

The script will prompt you to enter your Telegram `API ID`, `API Hash`, and the `target channel` or `group link`.

1. **API ID and API Hash**: You need to obtain these credentials from the [Telegram Developer Portal](https://my.telegram.org/apps).

2. **Target Channel or Group**: You can input the name or link of the Telegram group/channel you want to download from.

## Usage

Upon running the script, you will be prompted to enter your API credentials. Once connected, the script will:

1. Display the total number of messages in the group/channel.
2. Iterate through the messages and download all media matching specified file types.
3. Show the download progress via a progress bar and log messages in a scrollable text box.

## GUI Overview

- **Progress Label**: Shows connection status and current action.
- **Scrolled Text Log**: Displays ongoing status and any errors encountered.
- **Progress Bar**: Indicates overall download progress.

## Troubleshooting

- **Connection Issues**: If you see an error connecting to Telegram, ensure that your API credentials are correct.
- **Missing Dependencies**: Make sure to install all necessary Python packages from `requirements.txt`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Feel free to fork the project, submit pull requests, or create issues for any feature requests or bug reports.

## Acknowledgements

- **Telethon**: For providing an amazing library to interact with Telegram.
- **Tkinter**: For the simple yet effective GUI capabilities.

