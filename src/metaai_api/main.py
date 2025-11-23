import json
import logging
import time
import urllib.parse
import uuid
from typing import Dict, List, Generator, Iterator, Optional, Union

import requests
from requests_html import HTMLSession

from metaai_api.utils import (
    generate_offline_threading_id,
    extract_value,
    format_response,
)

from metaai_api.utils import get_fb_session, get_session

from metaai_api.exceptions import FacebookRegionBlocked

MAX_RETRIES = 3


class MetaAI:
    """
    A class to interact with the Meta AI API to obtain and use access tokens for sending
    and receiving messages from the Meta AI Chat API.
    """

    def __init__(
        self, fb_email: Optional[str] = None, fb_password: Optional[str] = None, cookies: Optional[dict] = None, proxy: Optional[dict] = None
    ):
        self.session = get_session()
        self.session.headers.update(
            {
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            }
        )
        self.access_token = None
        self.fb_email = fb_email
        self.fb_password = fb_password
        self.proxy = proxy

        self.is_authed = (fb_password is not None and fb_email is not None) or cookies is not None
        
        if cookies is not None:
            self.cookies = cookies
            # Auto-fetch lsd and fb_dtsg if not present in cookies
            if "lsd" not in self.cookies or "fb_dtsg" not in self.cookies:
                self._fetch_missing_tokens()
        else:
            self.cookies = self.get_cookies()
            
        self.external_conversation_id = None
        self.offline_threading_id = None

    def _fetch_missing_tokens(self):
        """
        Fetch lsd and fb_dtsg tokens if they're missing from cookies.
        """
        try:
            cookies_str = "; ".join([f"{k}={v}" for k, v in self.cookies.items() if v])
            
            session = HTMLSession()
            headers = {"cookie": cookies_str}
            response = session.get("https://www.meta.ai/", headers=headers)
            
            if "lsd" not in self.cookies:
                lsd = extract_value(response.text, start_str='"LSD",[],{"token":"', end_str='"')
                if lsd:
                    self.cookies["lsd"] = lsd
            
            if "fb_dtsg" not in self.cookies:
                fb_dtsg = extract_value(response.text, start_str='DTSGInitData",[],{"token":"', end_str='"')
                if fb_dtsg:
                    self.cookies["fb_dtsg"] = fb_dtsg
        except Exception as e:
            pass  # Silent fail, features may not work without tokens

    def get_access_token(self) -> str:
        """
        Retrieves an access token using Meta's authentication API.

        Returns:
            str: A valid access token.
        """

        if self.access_token:
            return self.access_token

        url = "https://www.meta.ai/api/graphql/"
        payload = {
            "lsd": self.cookies["lsd"],
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "useAbraAcceptTOSForTempUserMutation",
            "variables": {
                "dob": "1999-01-01",
                "icebreaker_type": "TEXT",
                "__relay_internal__pv__WebPixelRatiorelayprovider": 1,
            },
            "doc_id": "7604648749596940",
        }
        payload = urllib.parse.urlencode(payload)  # noqa
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "cookie": f'_js_datr={self.cookies["_js_datr"]}; '
            f'abra_csrf={self.cookies["abra_csrf"]}; datr={self.cookies["datr"]};',
            "sec-fetch-site": "same-origin",
            "x-fb-friendly-name": "useAbraAcceptTOSForTempUserMutation",
        }

        response = self.session.post(url, headers=headers, data=payload)

        try:
            auth_json = response.json()
        except json.JSONDecodeError:
            raise FacebookRegionBlocked(
                "Unable to receive a valid response from Meta AI. This is likely due to your region being blocked. "
                "Try manually accessing https://www.meta.ai/ to confirm."
            )

        access_token = auth_json["data"]["xab_abra_accept_terms_of_service"][
            "new_temp_user_auth"
        ]["access_token"]

        # Need to sleep for a bit, for some reason the API doesn't like it when we send request too quickly
        # (maybe Meta needs to register Cookies on their side?)
        time.sleep(1)

        return access_token

    def prompt(
        self,
        message: str,
        stream: bool = False,
        attempts: int = 0,
        new_conversation: bool = False,
        images: Optional[list] = None,
    ) -> Union[Dict, Generator[Dict, None, None]]:
        """
        Sends a message to the Meta AI and returns the response.

        Args:
            message (str): The message to send.
            stream (bool): Whether to stream the response or not. Defaults to False.
            attempts (int): The number of attempts to retry if an error occurs. Defaults to 0.
            new_conversation (bool): Whether to start a new conversation or not. Defaults to False.
            images (list): List of image URLs to animate (for video generation). Defaults to None.

        Returns:
            dict: A dictionary containing the response message and sources.

        Raises:
            Exception: If unable to obtain a valid response after several attempts.
        """
        if not self.is_authed:
            self.access_token = self.get_access_token()
            auth_payload = {"access_token": self.access_token}
            url = "https://graph.meta.ai/graphql?locale=user"

        else:
            auth_payload = {"fb_dtsg": self.cookies["fb_dtsg"]}
            url = "https://www.meta.ai/api/graphql/"

        if not self.external_conversation_id or new_conversation:
            external_id = str(uuid.uuid4())
            self.external_conversation_id = external_id
        
        # Handle video generation with images
        flash_video_input = {"images": []}
        if images:
            flash_video_input = {"images": images}
        
        payload = {
            **auth_payload,
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "useAbraSendMessageMutation",
            "variables": json.dumps(
                {
                    "message": {"sensitive_string_value": message},
                    "externalConversationId": self.external_conversation_id,
                    "offlineThreadingId": generate_offline_threading_id(),
                    "suggestedPromptIndex": None,
                    "flashVideoRecapInput": flash_video_input,
                    "flashPreviewInput": None,
                    "promptPrefix": None,
                    "entrypoint": "ABRA__CHAT__TEXT",
                    "icebreaker_type": "TEXT",
                    "__relay_internal__pv__AbraDebugDevOnlyrelayprovider": False,
                    "__relay_internal__pv__WebPixelRatiorelayprovider": 1,
                }
            ),
            "server_timestamps": "true",
            "doc_id": "7783822248314888",
        }
        payload = urllib.parse.urlencode(payload)  # noqa
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "x-fb-friendly-name": "useAbraSendMessageMutation",
        }
        if self.is_authed:
            headers["cookie"] = f'abra_sess={self.cookies["abra_sess"]}'
            # Recreate the session to avoid cookie leakage when user is authenticated
            self.session = requests.Session()
            if self.proxy:
                self.session.proxies = self.proxy

        response = self.session.post(url, headers=headers, data=payload, stream=stream)
        if not stream:
            raw_response = response.text
            last_streamed_response = self.extract_last_response(raw_response)
            if not last_streamed_response:
                return self.retry(message, stream=stream, attempts=attempts)

            extracted_data = self.extract_data(last_streamed_response)
            return extracted_data

        else:
            lines = response.iter_lines()
            is_error = json.loads(next(lines))
            if len(is_error.get("errors", [])) > 0:
                return self.retry(message, stream=stream, attempts=attempts)
            return self.stream_response(lines)

    def retry(self, message: str, stream: bool = False, attempts: int = 0):
        """
        Retries the prompt function if an error occurs.
        """
        if attempts <= MAX_RETRIES:
            logging.warning(
                f"Was unable to obtain a valid response from Meta AI. Retrying... Attempt {attempts + 1}/{MAX_RETRIES}."
            )
            time.sleep(3)
            return self.prompt(message, stream=stream, attempts=attempts + 1)
        else:
            raise Exception(
                "Unable to obtain a valid response from Meta AI. Try again later."
            )

    def extract_last_response(self, response: str) -> Optional[Dict]:
        """
        Extracts the last response from the Meta AI API.

        Args:
            response (str): The response to extract the last response from.

        Returns:
            dict: A dictionary containing the last response.
        """
        last_streamed_response = None
        for line in response.split("\n"):
            try:
                json_line = json.loads(line)
            except json.JSONDecodeError:
                continue

            bot_response_message = (
                json_line.get("data", {})
                .get("node", {})
                .get("bot_response_message", {})
            )
            chat_id = bot_response_message.get("id")
            if chat_id:
                external_conversation_id, offline_threading_id, _ = chat_id.split("_")
                self.external_conversation_id = external_conversation_id
                self.offline_threading_id = offline_threading_id

            streaming_state = bot_response_message.get("streaming_state")
            if streaming_state == "OVERALL_DONE":
                last_streamed_response = json_line

        return last_streamed_response

    def stream_response(self, lines: Iterator[str]):
        """
        Streams the response from the Meta AI API.

        Args:
            lines (Iterator[str]): The lines to stream.

        Yields:
            dict: A dictionary containing the response message and sources.
        """
        for line in lines:
            if line:
                json_line = json.loads(line)
                extracted_data = self.extract_data(json_line)
                if not extracted_data.get("message"):
                    continue
                yield extracted_data

    def extract_data(self, json_line: dict):
        """
        Extract data and sources from a parsed JSON line.

        Args:
            json_line (dict): Parsed JSON line.

        Returns:
            Tuple (str, list): Response message and list of sources.
        """
        bot_response_message = (
            json_line.get("data", {}).get("node", {}).get("bot_response_message", {})
        )
        response = format_response(response=json_line)
        fetch_id = bot_response_message.get("fetch_id")
        sources = self.fetch_sources(fetch_id) if fetch_id else []
        medias = self.extract_media(bot_response_message)
        return {"message": response, "sources": sources, "media": medias}

    @staticmethod
    def extract_media(json_line: dict) -> List[Dict]:
        """
        Extract media from a parsed JSON line.
        Supports images from imagine_card and videos from various fields.

        Args:
            json_line (dict): Parsed JSON line.

        Returns:
            list: A list of dictionaries containing the extracted media.
        """
        medias = []
        
        # Extract images from imagine_card (standard image generation)
        imagine_card = json_line.get("imagine_card", {})
        session = imagine_card.get("session", {}) if imagine_card else {}
        media_sets = (
            (json_line.get("imagine_card", {}).get("session", {}).get("media_sets", []))
            if imagine_card and session
            else []
        )
        for media_set in media_sets:
            imagine_media = media_set.get("imagine_media", [])
            for media in imagine_media:
                medias.append(
                    {
                        "url": media.get("uri"),
                        "type": media.get("media_type"),
                        "prompt": media.get("prompt"),
                    }
                )
        
        # Extract from image_attachments (may contain both images and videos)
        image_attachments = json_line.get("image_attachments", [])
        if isinstance(image_attachments, list):
            for attachment in image_attachments:
                if isinstance(attachment, dict):
                    # Check for video URLs
                    uri = attachment.get("uri") or attachment.get("url")
                    if uri:
                        media_type = "VIDEO" if ".mp4" in uri.lower() or ".m4v" in uri.lower() else "IMAGE"
                        medias.append(
                            {
                                "url": uri,
                                "type": media_type,
                                "prompt": attachment.get("prompt"),
                            }
                        )
        
        # Extract videos from video_generation field (if present)
        video_generation = json_line.get("video_generation", {})
        if isinstance(video_generation, dict):
            video_media_sets = video_generation.get("media_sets", [])
            for media_set in video_media_sets:
                video_media = media_set.get("video_media", [])
                for media in video_media:
                    uri = media.get("uri")
                    if uri:  # Only add if URI is not null
                        medias.append(
                            {
                                "url": uri,
                                "type": "VIDEO",
                                "prompt": media.get("prompt"),
                            }
                        )
        
        # Extract from direct video fields
        for possible_video_field in ["video_media", "generated_video", "reels"]:
            field_data = json_line.get(possible_video_field)
            if field_data:
                if isinstance(field_data, list):
                    for item in field_data:
                        if isinstance(item, dict) and ("uri" in item or "url" in item):
                            url = item.get("uri") or item.get("url")
                            if url:  # Only add if URL is not null
                                medias.append(
                                    {
                                        "url": url,
                                        "type": "VIDEO",
                                        "prompt": item.get("prompt"),
                                    }
                                )
        
        return medias

    def get_cookies(self) -> dict:
        """
        Extracts necessary cookies from the Meta AI main page.

        Returns:
            dict: A dictionary containing essential cookies.
        """
        session = HTMLSession()
        headers = {}
        fb_session = None
        if self.fb_email is not None and self.fb_password is not None:
            fb_session = get_fb_session(self.fb_email, self.fb_password)
            headers = {"cookie": f"abra_sess={fb_session['abra_sess']}"}
        response = session.get(
            "https://www.meta.ai/",
            headers=headers,
        )
        cookies = {
            "_js_datr": extract_value(
                response.text, start_str='_js_datr":{"value":"', end_str='",'
            ),
            "datr": extract_value(
                response.text, start_str='datr":{"value":"', end_str='",'
            ),
            "lsd": extract_value(
                response.text, start_str='"LSD",[],{"token":"', end_str='"}'
            ),
            "fb_dtsg": extract_value(
                response.text, start_str='DTSGInitData",[],{"token":"', end_str='"'
            ),
        }

        if len(headers) > 0 and fb_session is not None:
            cookies["abra_sess"] = fb_session["abra_sess"]
        else:
            cookies["abra_csrf"] = extract_value(
                response.text, start_str='abra_csrf":{"value":"', end_str='",'
            )
        return cookies

    def fetch_sources(self, fetch_id: str) -> List[Dict]:
        """
        Fetches sources from the Meta AI API based on the given query.

        Args:
            fetch_id (str): The fetch ID to use for the query.

        Returns:
            list: A list of dictionaries containing the fetched sources.
        """

        url = "https://graph.meta.ai/graphql?locale=user"
        payload = {
            "access_token": self.access_token,
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "AbraSearchPluginDialogQuery",
            "variables": json.dumps({"abraMessageFetchID": fetch_id}),
            "server_timestamps": "true",
            "doc_id": "6946734308765963",
        }

        payload = urllib.parse.urlencode(payload)  # noqa

        headers = {
            "authority": "graph.meta.ai",
            "accept-language": "en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
            "cookie": f'dpr=2; abra_csrf={self.cookies.get("abra_csrf")}; datr={self.cookies.get("datr")}; ps_n=1; ps_l=1',
            "x-fb-friendly-name": "AbraSearchPluginDialogQuery",
        }

        response = self.session.post(url, headers=headers, data=payload)
        response_json = response.json()
        message = response_json.get("data", {}).get("message", {})
        search_results = (
            (response_json.get("data", {}).get("message", {}).get("searchResults"))
            if message
            else None
        )
        if search_results is None:
            return []

        references = search_results["references"]
        return references

    def generate_video(
        self,
        prompt: str,
        wait_before_poll: int = 10,
        max_attempts: int = 30,
        wait_seconds: int = 5,
        verbose: bool = True
    ) -> Dict:
        """
        Generate a video from a text prompt using Meta AI.
        Automatically fetches lsd and fb_dtsg tokens from cookies.

        Args:
            prompt: Text prompt for video generation
            wait_before_poll: Seconds to wait before starting to poll (default: 10)
            max_attempts: Maximum polling attempts (default: 30)
            wait_seconds: Seconds between polling attempts (default: 5)
            verbose: Whether to print status messages (default: True)

        Returns:
            Dictionary with success status, conversation_id, prompt, video_urls, and timestamp

        Example:
            ai = MetaAI(cookies={"datr": "...", "abra_sess": "..."})
            result = ai.generate_video("Generate a video of a sunset")
            if result["success"]:
                print(f"Video URLs: {result['video_urls']}")
        """
        from metaai_api.video_generation import VideoGenerator
        
        # Convert cookies dict to string format if needed
        if isinstance(self.cookies, dict):
            cookies_str = "; ".join([f"{k}={v}" for k, v in self.cookies.items() if v])
        else:
            cookies_str = str(self.cookies)
        
        # Use VideoGenerator for video generation
        video_gen = VideoGenerator(cookies_str=cookies_str)
        
        return video_gen.generate_video(
            prompt=prompt,
            wait_before_poll=wait_before_poll,
            max_attempts=max_attempts,
            wait_seconds=wait_seconds,
            verbose=verbose
        )


if __name__ == "__main__":
    meta = MetaAI()
    resp = meta.prompt("What was the Warriors score last game?", stream=False)
    print(resp)
