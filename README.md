# Telegram Media Downloader

## Description
Telegram Media Downloader is a simple application that allows you to download various types of media files from Telegram channels. The application supports downloading PDFs, images (JPEG, PNG), videos (MP4), as well as any other file types.

This project also includes an EXE version so you can run the program without having Python installed.

## Features
- **Simple Graphical User Interface (GUI):** Easily download media from your Telegram channels.
- **Configuration Settings:** Save your API credentials and target channel details.
- **Supported File Types:** Choose to download PDFs, images, videos, or all file types.
- **Logging:** View detailed logs of the download process.
- **Standalone EXE:** The compiled EXE file can be found in the `dist` folder.

## How to Run the EXE
1. Open the `dist` folder, where the generated `.exe` file is located.
2. Double-click the executable to launch the application.

## Usage Guide
1. Launch the application.
2. Navigate to the **Settings** menu and enter the required details:
   - **API ID** and **API Hash:** Obtain these from the [Telegram Developer Portal](https://my.telegram.org).
   - **Target Channel:** The name or link of the Telegram channel you want to download from.
3. Select the desired file type (PDF, images, videos, or all files).
4. Click the **Save** button to store your configuration.
5. Return to the **Download** tab and wait for the application to connect to the Telegram channel and download the selected files.

## Important Notes
- **Telegram API Credentials:** You must provide a valid Telegram API ID and API Hash. You can get these from the [Telegram Developer Portal](https://my.telegram.org).
- **Troubleshooting:** If an error occurs during the download process, check your channel details and API credentials.

## For Developers
If you wish to modify the source code:
- Clone the repository from GitHub.
- Make sure all required Python packages are installed (check the `requirements.txt` file if provided).

## Contributing
Contributions are welcome! Please open a pull request or submit your ideas and issues via the GitHub Issues section.

## License
This project is available under the [MIT License](LICENSE).
