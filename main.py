import argparse
import logging
from argparse import ArgumentError
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.file_detector import LocalFileDetector

from src import exceptions

from src.login import confirm_logged_in, login_using_cookie_file
from src.upload import upload_file


def main():
    logging.getLogger().setLevel(logging.INFO)

    # Setup Selenium web driver
    parser = get_arg_parser()
    args = parser.parse_args()

    if args.browser == "docker":
        driver = webdriver.Remote(
            command_executor="http://127.0.0.1:4444/wd/hub",
            desired_capabilities=DesiredCapabilities.FIREFOX,
        )
    elif args.browser == "firefox":
        firefox_profile = webdriver.FirefoxProfile()
        firefox_profile.set_preference("intl.accept_languages", "en-us")
        firefox_profile.update_preferences()
        driver = webdriver.Firefox(firefox_profile)
    elif args.browser == "chrome":
        if args.headless:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--start-maximized')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36')
            driver = webdriver.Chrome(options=options)
        else:
            driver = webdriver.Chrome()
    else:
        raise ArgumentError(message="Unknown driver.")

    driver.set_window_size(1920, 1080)
    login_using_cookie_file(driver, cookie_file=args.login_cookies)
    driver.get("https://www.youtube.com")

    assert "YouTube" in driver.title

    try:
        confirm_logged_in(driver)
        driver.get("https://studio.youtube.com")
        assert "Channel dashboard" in driver.title
        driver.file_detector = LocalFileDetector()
        upload_file(
            driver,
            video_path=args.video_path,
            title=args.title,
            thumbnail_path=args.thumbnail,
            description=args.description,
            game=args.game,
            kids=args.kids,
            upload_time=args.upload_time,
        )
    except (exceptions.DailyUploadLimitReachedException):
        driver.close()
        exit(1)
    except:
        driver.close()
        raise


def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    today = datetime.now()
    parser.add_argument(
        "-B",
        "--browser",
        choices=["docker", "chrome", "firefox"],
        default="docker",
        type=str,
        help="Select the driver/browser to use for executing the script (default: docker).",
    )
    parser.add_argument(
        "-hl",
        "--headless",
        required=False,
        action="store_true",
        help="Select whether to run the browser in headless(GUI-less) mode. Currently for Chrome only.",
    )
    parser.add_argument(
        "-l",
        "--login-cookies-path",
        dest="login_cookies",
        type=str,
        help="A json file that contains the cookies required to sign into YouTube in the target browser.",
        required=True,
    )
    parser.add_argument(
        "video_path",
        help="Path to the video file. When using docker, this path has to be inside the container "
             "(default mount is /uploads/).",
    )
    parser.add_argument(
        "--thumbnail-path",
        "-T",
        help="Path to the thumbnail file (default: None).",
        dest="thumbnail",
        type=str,
        default=None,
        required=False,
    )
    parser.add_argument(
        "-t",
        "--title",
        help="This argument declares the title of the uploaded video.",
        type=str,
        default=None,
        required=False,
    )
    parser.add_argument(
        "-d",
        "--description",
        help="This argument declares the description of the uploaded video.",
        type=str,
        default=None,
        required=False,
    )
    parser.add_argument(
        "-g",
        "--game",
        help="This argument declares the game of the uploaded video (default: None).",
        default=None,
        required=False,
    )
    parser.add_argument(
        "-k",
        "--kids",
        help="Whether the video is made for kids or not. (default: False)",
        required=False,
        type=bool,
        default=False,
    )
    parser.add_argument(
        "-ut",
        "--upload_time",
        help="This argument declares the scheduled upload time (UTC) of the uploaded video. "
             "(Example: 2021-04-04T20:00:00)",
        required=False,
        type=datetime.fromisoformat,
        default=None,
    )
    return parser


if __name__ == "__main__":
    main()
