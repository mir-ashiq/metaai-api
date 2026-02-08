import json
import logging
import time
import urllib.parse
import uuid
from typing import Dict, List, Generator, Iterator, Optional, Union, Any

import requests
from requests_html import HTMLSession

from metaai_api.utils import (
    generate_offline_threading_id,
    extract_value,
    format_response,
    detect_challenge_page,
    handle_meta_ai_challenge,
)

from metaai_api.utils import get_fb_session, get_session

from metaai_api.exceptions import FacebookRegionBlocked
from metaai_api.image_upload import ImageUploader
from metaai_api.generation import GenerationAPI

MAX_RETRIES = 3


class MetaAI:
    """
    A class to interact with the Meta AI API to obtain and use access tokens for sending
    and receiving messages from the Meta AI Chat API.
    """

    def __init__(
        self, 
        fb_email: Optional[str] = None, 
        fb_password: Optional[str] = None, 
        cookies: Optional[dict] = None, 
        proxy: Optional[dict] = None,
        lsd: Optional[str] = None,
        fb_dtsg: Optional[str] = None
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
            # Add manually provided tokens if available
            if lsd:
                self.cookies["lsd"] = lsd
            if fb_dtsg:
                self.cookies["fb_dtsg"] = fb_dtsg
            # Auto-fetch lsd and fb_dtsg if not present in cookies
            if "lsd" not in self.cookies or "fb_dtsg" not in self.cookies:
                self._fetch_missing_tokens()
        else:
            self.cookies = self.get_cookies()
            # Override with manually provided tokens if available
            if lsd:
                self.cookies["lsd"] = lsd
            if fb_dtsg:
                self.cookies["fb_dtsg"] = fb_dtsg
            # Update is_authed if we successfully got cookies
            if self.cookies and "lsd" in self.cookies and "fb_dtsg" in self.cookies:
                self.is_authed = True
            
        self.external_conversation_id = None
        self.offline_threading_id = None
        
        # Initialize Generation API
        self.generation_api = GenerationAPI(session=self.session, cookies=self.cookies)

    def _fetch_missing_tokens(self, max_retries: int = 3):
        """
        Fetch lsd and fb_dtsg tokens if they're missing from cookies.
        Handles Meta AI challenge pages automatically.
        
        Args:
            max_retries (int): Maximum number of retry attempts.
        """
        try:
            session = HTMLSession()
            # Set cookies on session object (not as header string)
            session.cookies.update(self.cookies)
            
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
            
            for attempt in range(max_retries):
                logging.info(f"Fetching tokens from Meta AI (attempt {attempt + 1}/{max_retries})...")
                response = session.get("https://meta.ai", headers=headers)
                
                # Check if we got a challenge page
                challenge_url = detect_challenge_page(response.text)
                if challenge_url:
                    logging.warning(f"Meta AI returned a challenge page. Challenge URL: {challenge_url}")
                    logging.warning(f"Calling handle_meta_ai_challenge with cookies_dict keys: {list(self.cookies.keys())}")
                    challenge_result = handle_meta_ai_challenge(session, challenge_url=challenge_url, cookies_dict=self.cookies)
                    logging.warning(f"Challenge handling result: {challenge_result}")
                    if challenge_result:
                        # Retry fetching tokens after handling challenge
                        logging.warning("Re-fetching tokens after challenge resolution...")
                        logging.warning(f"Cookies after challenge: {list(self.cookies.keys())}")
                        response = session.get("https://meta.ai", headers=headers)
                    else:
                        logging.error("Failed to handle Meta AI challenge.")
                        if attempt < max_retries - 1:
                            logging.warning("Retrying...")
                            time.sleep(2)
                            continue
                        else:
                            logging.error("Max retries reached. Aborting token fetch.")
                            break
                
                # Extract tokens from HTTP response - try multiple patterns
                if "lsd" not in self.cookies:
                    # Try JavaScript pattern first (original method)
                    lsd = extract_value(response.text, start_str='"LSD",[],{"token":"', end_str='"}')  
                    
                    # If not found, try HTML input field pattern
                    if not lsd:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(response.text, 'html.parser')
                        lsd_input = soup.find("input", {"name": "lsd"})
                        if lsd_input and lsd_input.get("value"):
                            lsd = lsd_input["value"]  # type: ignore
                    
                    if lsd:
                        self.cookies["lsd"] = lsd
                        logging.info("Successfully fetched lsd token.")
                    else:
                        logging.warning("Could not extract lsd token from response.")
                
                if "fb_dtsg" not in self.cookies:
                    # Try JavaScript pattern first (original method)
                    fb_dtsg = extract_value(response.text, start_str='DTSGInitData",[],{"token":"', end_str='"')
                    
                    # If not found, try alternative patterns
                    if not fb_dtsg:
                        fb_dtsg = extract_value(response.text, start_str='"DTSGInitialData",[],{"token":"', end_str='"')
                    if not fb_dtsg:
                        fb_dtsg = extract_value(response.text, start_str='{"token":"', end_str='","async_get_token"')
                    
                    if fb_dtsg:
                        self.cookies["fb_dtsg"] = fb_dtsg
                        logging.info("Successfully fetched fb_dtsg token.")
                    else:
                        logging.warning("Could not extract fb_dtsg token from response.")
                    if fb_dtsg:
                        self.cookies["fb_dtsg"] = fb_dtsg
                        logging.info("Successfully fetched fb_dtsg token.")
                    else:
                        logging.warning("Could not extract fb_dtsg token from response.")
                
                # Check if we got both tokens
                if ("lsd" in self.cookies and self.cookies["lsd"]) and \
                   ("fb_dtsg" in self.cookies and self.cookies["fb_dtsg"]):
                    logging.info("Token fetch completed successfully.")
                    break
                    
                if attempt < max_retries - 1:
                    logging.warning(f"Tokens not fully fetched. Retrying in 2 seconds...")
                    time.sleep(2)
                    
        except Exception as e:
            logging.error(f"Error fetching tokens: {e}")
            logging.warning("Some features may not work without lsd/fb_dtsg tokens.")
            logging.info("Consider manually providing 'lsd' and 'fb_dtsg' tokens in the MetaAI constructor.")

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
        media_ids: Optional[list] = None,
        attachment_metadata: Optional[Dict[str, Any]] = None,
        is_image_generation: bool = False,
        orientation: Optional[str] = None,
    ) -> Union[Dict, Generator[Dict, None, None]]:
        """
        Sends a message to the Meta AI and returns the response.

        Args:
            message (str): The message to send.
            stream (bool): Whether to stream the response or not. Defaults to False.
            attempts (int): The number of attempts to retry if an error occurs. Defaults to 0.
            new_conversation (bool): Whether to start a new conversation or not. Defaults to False.
            images (list): List of image URLs to animate (for video generation). Defaults to None.
            media_ids (list): List of media IDs from uploaded images to include in the prompt. Defaults to None.
            attachment_metadata (dict): Optional dict with 'file_size' (int) and 'mime_type' (str). Defaults to None.
            is_image_generation (bool): Whether this is for image generation (vs chat). Defaults to False.
            orientation (str): Image orientation for generation. Valid values: "LANDSCAPE", "VERTICAL", "SQUARE". Defaults to "VERTICAL".

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
            auth_payload = {
                "fb_dtsg": self.cookies["fb_dtsg"],
                "lsd": self.cookies.get("lsd", ""),
            }
            url = "https://www.meta.ai/api/graphql/"

        if not self.external_conversation_id or new_conversation:
            external_id = str(uuid.uuid4())
            self.external_conversation_id = external_id
        
        # Handle video generation with images
        flash_video_input = {"images": []}
        if images:
            flash_video_input = {"images": images}
        
        # Handle uploaded media attachments
        attachments_v2 = []
        if media_ids:
            attachments_v2 = [str(mid) for mid in media_ids]
        
        # Generate offline threading IDs
        offline_threading_id = generate_offline_threading_id()
        bot_offline_threading_id = str(int(offline_threading_id) + 1)
        thread_session_id = str(uuid.uuid4())
        
        # Determine entrypoint based on context
        if images:
            # Video generation with images uses CHAT
            entrypoint = "KADABRA__CHAT__UNIFIED_INPUT_BAR"
        elif media_ids or orientation:
            # Image generation with orientation OR uploaded images uses DISCOVER
            entrypoint = "KADABRA__DISCOVER__UNIFIED_INPUT_BAR"
        else:
            entrypoint = "ABRA__CHAT__TEXT"
        
        # Set friendly name based on entrypoint
        friendly_name = "useKadabraSendMessageMutation" if entrypoint.startswith("KADABRA") else "useAbraSendMessageMutation"
        
        # Build variables dictionary
        is_kadabra = entrypoint.startswith("KADABRA")
        
        if is_kadabra:
            # Full Kadabra variables for image generation
            variables = {
                "message": {"sensitive_string_value": message},
                "externalConversationId": self.external_conversation_id,
                "offlineThreadingId": offline_threading_id,
                "threadSessionId": thread_session_id,
                "isNewConversation": new_conversation or not self.offline_threading_id,
                "suggestedPromptIndex": None,
                "promptPrefix": None,
                "entrypoint": entrypoint,
                "attachments": [],
                "attachmentsV2": attachments_v2,
                "activeMediaSets": [],
                "activeCardVersions": [],
                "activeArtifactVersion": None,
                "userUploadEditModeInput": None,
                "reelComposeInput": None,
                "qplJoinId": uuid.uuid4().hex[:17],
                "sourceRemixPostId": None,
                "gkPlannerOrReasoningEnabled": True,
                "selectedModel": "BASIC_OPTION",
                "conversationMode": None,
                "selectedAgentType": "PLANNER",
                "agentSettings": None,
                "conversationStarterId": None,
                "promptType": None,
                "artifactRewriteOptions": None,
                "imagineOperationRequest": None,
                "imagineClientOptions": {"orientation": str(orientation).upper() if orientation else "VERTICAL"},
                "spaceId": None,
                "sparkSnapshotId": None,
                "topicPageId": None,
                "includeSpace": False,
                "storybookId": None,
                "messagePersistentInput": {
                    "attachment_size": attachment_metadata.get('file_size') if attachment_metadata else None,
                    "attachment_type": attachment_metadata.get('mime_type') if attachment_metadata else None,
                    "bot_message_offline_threading_id": bot_offline_threading_id,
                    "conversation_mode": None,
                    "external_conversation_id": self.external_conversation_id,
                    "is_new_conversation": new_conversation or not self.offline_threading_id,
                    "meta_ai_entry_point": entrypoint,
                    "offline_threading_id": offline_threading_id,
                    "prompt_id": None,
                    "prompt_session_id": thread_session_id,
                },
                "alakazam_enabled": True,
                "skipInFlightMessageWithParams": None,
                "__relay_internal__pv__KadabraSocialSearchEnabledrelayprovider": False,
                "__relay_internal__pv__KadabraZeitgeistEnabledrelayprovider": False,
                "__relay_internal__pv__alakazam_enabledrelayprovider": True,
                "__relay_internal__pv__sp_kadabra_survey_invitationrelayprovider": True,
                "__relay_internal__pv__enable_kadabra_partial_resultsrelayprovider": False,
                "__relay_internal__pv__AbraArtifactsEnabledrelayprovider": True,
                "__relay_internal__pv__KadabraMemoryEnabledrelayprovider": False,
                "__relay_internal__pv__AbraPlannerEnabledrelayprovider": True,
                "__relay_internal__pv__AbraWidgetsEnabledrelayprovider": False,
                "__relay_internal__pv__KadabraDeepResearchEnabledrelayprovider": False,
                "__relay_internal__pv__KadabraThinkHarderEnabledrelayprovider": False,
                "__relay_internal__pv__KadabraVergeEnabledrelayprovider": False,
                "__relay_internal__pv__KadabraSpacesEnabledrelayprovider": False,
                "__relay_internal__pv__KadabraProductSearchEnabledrelayprovider": False,
                "__relay_internal__pv__KadabraAreServiceEnabledrelayprovider": False,
                "__relay_internal__pv__kadabra_render_reasoning_response_statesrelayprovider": True,
                "__relay_internal__pv__kadabra_reasoning_cotrelayprovider": False,
                "__relay_internal__pv__AbraSearchInlineReferencesEnabledrelayprovider": True,
                "__relay_internal__pv__AbraComposedTextWidgetsrelayprovider": True,
                "__relay_internal__pv__KadabraNewCitationsEnabledrelayprovider": True,
                "__relay_internal__pv__WebPixelRatiorelayprovider": 1,
                "__relay_internal__pv__KadabraVideoDeliveryRequestrelayprovider": {
                    "dash_manifest_requests": [{}],
                    "progressive_url_requests": [{"quality": "HD"}, {"quality": "SD"}]
                },
                "__relay_internal__pv__KadabraWidgetsRedesignEnabledrelayprovider": False,
                "__relay_internal__pv__kadabra_enable_send_message_retryrelayprovider": True,
                "__relay_internal__pv__KadabraEmailCalendarIntegrationrelayprovider": False,
                "__relay_internal__pv__ClippyUIrelayprovider": False,
                "__relay_internal__pv__kadabra_reels_connect_featuresrelayprovider": False,
                "__relay_internal__pv__AbraBugNubrelayprovider": False,
                "__relay_internal__pv__AbraRedteamingrelayprovider": False,
                "__relay_internal__pv__AbraDebugDevOnlyrelayprovider": False,
                "__relay_internal__pv__kadabra_enable_open_in_editor_message_actionrelayprovider": True,
                "__relay_internal__pv__BloksDeviceContextrelayprovider": {"pixel_ratio": 1},
                "__relay_internal__pv__AbraThreadsEnabledrelayprovider": False,
                "__relay_internal__pv__kadabra_story_builder_enabledrelayprovider": False,
                "__relay_internal__pv__kadabra_imagine_canvas_enable_dev_settingsrelayprovider": False,
                "__relay_internal__pv__kadabra_create_media_deletionrelayprovider": False,
                "__relay_internal__pv__kadabra_moodboardrelayprovider": False,
                "__relay_internal__pv__AbraArtifactDragImagineFromConversationrelayprovider": True,
                "__relay_internal__pv__kadabra_media_item_renderer_heightrelayprovider": 545,
                "__relay_internal__pv__kadabra_media_item_renderer_widthrelayprovider": 620,
                "__relay_internal__pv__AbraQPDocUploadNuxTriggerNamerelayprovider": "meta_dot_ai_abra_web_doc_upload_nux_tour",
                "__relay_internal__pv__AbraSurfaceNuxIDrelayprovider": "12177",
                "__relay_internal__pv__KadabraConversationRenamingrelayprovider": True,
                "__relay_internal__pv__AbraIsLoggedOutrelayprovider": not self.is_authed,
                "__relay_internal__pv__KadabraCanvasDisplayHeaderV2relayprovider": False,
                "__relay_internal__pv__AbraArtifactEditorDebugModerelayprovider": False,
                "__relay_internal__pv__AbraArtifactEditorDownloadHTMLEnabledrelayprovider": False,
                "__relay_internal__pv__kadabra_create_row_hover_optionsrelayprovider": False,
                "__relay_internal__pv__kadabra_media_info_pillsrelayprovider": True,
                "__relay_internal__pv__KadabraConcordInternalProfileBadgeEnabledrelayprovider": False,
                "__relay_internal__pv__KadabraSocialGraphrelayprovider": True,
            }
        else:
            # Simpler Abra variables for chat
            variables = {
                "message": {"sensitive_string_value": message},
                "externalConversationId": self.external_conversation_id,
                "offlineThreadingId": offline_threading_id,
                "suggestedPromptIndex": None,
                "flashVideoRecapInput": flash_video_input,
                "flashPreviewInput": None,
                "promptPrefix": None,
                "entrypoint": entrypoint,
                "attachments": [],
                "attachmentsV2": attachments_v2,
                "messagePersistentInput": {
                    "attachment_size": attachment_metadata.get('file_size') if attachment_metadata else None,
                    "attachment_type": attachment_metadata.get('mime_type') if attachment_metadata else None,
                    "external_conversation_id": self.external_conversation_id,
                    "offline_threading_id": offline_threading_id,
                    "meta_ai_entry_point": entrypoint,
                } if media_ids else None,
                "icebreaker_type": "TEXT",
                "__relay_internal__pv__AbraDebugDevOnlyrelayprovider": False,
                "__relay_internal__pv__WebPixelRatiorelayprovider": 1,
            }
        
        payload = {
            **auth_payload,
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": friendly_name,
            "variables": json.dumps(variables),
            "server_timestamps": "true",
            "doc_id": "24895882500088854" if is_kadabra else "7783822248314888",
        }
        payload = urllib.parse.urlencode(payload)  # noqa
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "x-fb-friendly-name": friendly_name,
        }
        # Add lsd header for authenticated requests
        if self.cookies.get("lsd"):
            headers["x-fb-lsd"] = self.cookies["lsd"]
        if self.is_authed and "abra_sess" in self.cookies:
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
                return self.retry(message, stream=stream, attempts=attempts, new_conversation=new_conversation, images=images, media_ids=media_ids, attachment_metadata=attachment_metadata, is_image_generation=is_image_generation, orientation=orientation)

            extracted_data = self.extract_data(last_streamed_response)
            return extracted_data

        else:
            lines = response.iter_lines()
            is_error = json.loads(next(lines))
            if len(is_error.get("errors", [])) > 0:
                return self.retry(message, stream=stream, attempts=attempts, new_conversation=new_conversation, images=images, media_ids=media_ids, attachment_metadata=attachment_metadata, is_image_generation=is_image_generation, orientation=orientation)
            return self.stream_response(lines)

    def retry(self, message: str, stream: bool = False, attempts: int = 0, new_conversation: bool = False, images: Optional[list] = None, media_ids: Optional[list] = None, attachment_metadata: Optional[Dict[str, Any]] = None, is_image_generation: bool = False, orientation: Optional[str] = None):
        """
        Retries the prompt function if an error occurs.
        """
        if attempts <= MAX_RETRIES:
            logging.warning(
                f"Was unable to obtain a valid response from Meta AI. Retrying... Attempt {attempts + 1}/{MAX_RETRIES}."
            )
            time.sleep(3)
            return self.prompt(message, stream=stream, attempts=attempts + 1, new_conversation=new_conversation, images=images, media_ids=media_ids, attachment_metadata=attachment_metadata, is_image_generation=is_image_generation, orientation=orientation)
        else:
            raise Exception(
                "Unable to obtain a valid response from Meta AI. Try again later."
            )

    def extract_last_response(self, response: str) -> Optional[Dict]:
        """
        Extracts the last response from the Meta AI API.
        Handles both Abra and Kadabra response structures.

        Args:
            response (str): The response to extract the last response from.

        Returns:
            dict: A dictionary containing the last response.
        """
        last_streamed_response = None
        all_responses = []
        
        for line in response.split("\n"):
            try:
                json_line = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Store all valid JSON responses
            all_responses.append(json_line)
            
            bot_response_message = (
                json_line.get("data", {})
                .get("node", {})
                .get("bot_response_message", {})
            )
            
            if not bot_response_message:
                # Try alternative structure for Kadabra
                bot_response_message = (
                    json_line.get("data", {})
                    .get("message", {})
                )
            
            chat_id = bot_response_message.get("id")
            if chat_id:
                try:
                    external_conversation_id, offline_threading_id, _ = chat_id.split("_")
                    self.external_conversation_id = external_conversation_id
                    self.offline_threading_id = offline_threading_id
                except:
                    pass

            streaming_state = bot_response_message.get("streaming_state")
            if streaming_state == "OVERALL_DONE":
                last_streamed_response = json_line
        
        # If no OVERALL_DONE found, use the last non-empty response
        if not last_streamed_response and all_responses:
            # Find last response with actual content
            for resp in reversed(all_responses):
                if resp.get("data", {}).get("node", {}).get("bot_response_message", {}):
                    last_streamed_response = resp
                    break
                elif resp.get("data", {}).get("message", {}):
                    # Kadabra structure
                    last_streamed_response = resp
                    break

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
        Handles both Abra and Kadabra response structures.

        Args:
            json_line (dict): Parsed JSON line.

        Returns:
            Tuple (str, list): Response message and list of sources.
        """
        # Try standard Abra structure first
        bot_response_message = (
            json_line.get("data", {}).get("node", {}).get("bot_response_message", {})
        )
        
        # If empty, try Kadabra structure
        if not bot_response_message:
            bot_response_message = json_line.get("data", {}).get("message", {})
        
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
        
        # Extract images from content.imagine.session (has full URLs)
        # This is the primary location with complete media information
        content = json_line.get("content", {})
        imagine = content.get("imagine", {})
        session = imagine.get("session", {})
        media_sets = session.get("media_sets", [])
        
        if media_sets:
            # Found full imagine data with URIs
            for media_set in media_sets:
                imagine_media = media_set.get("imagine_media", [])
                for media in imagine_media:
                    # Try multiple possible URL fields
                    url = (media.get("uri") or 
                           media.get("image_uri") or 
                           media.get("maybe_image_uri") or
                           media.get("url"))
                    if url:  # Only add if URL is found
                        medias.append(
                            {
                                "url": url,
                                "type": media.get("media_type"),
                                "prompt": media.get("prompt"),
                            }
                        )
        else:
            # Fallback: Try imagine_card.session (may not have full URLs)
            imagine_card = json_line.get("imagine_card", {})
            if imagine_card:
                session = imagine_card.get("session", {})
                media_sets = session.get("media_sets", []) if session else []
                for media_set in media_sets:
                    imagine_media = media_set.get("imagine_media", [])
                    for media in imagine_media:
                        url = (media.get("uri") or 
                               media.get("image_uri") or 
                               media.get("maybe_image_uri") or
                               media.get("url"))
                        if url:
                            medias.append(
                                {
                                    "url": url,
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
        Handles challenge pages automatically.

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
            "https://meta.ai",
            headers=headers,
        )
        
        # Check for challenge page
        challenge_url = detect_challenge_page(response.text)
        if challenge_url:
            logging.warning("⚠️  Meta AI returned a challenge page during get_cookies. Attempting to handle it...")
            cookies_dict = {}
            if fb_session:
                cookies_dict = {"abra_sess": fb_session["abra_sess"]}
            if handle_meta_ai_challenge(session, challenge_url=challenge_url, cookies_dict=cookies_dict):
                # Retry after handling challenge
                logging.info("🔄 Re-fetching cookies after challenge resolution...")
                response = session.get("https://meta.ai", headers=headers)
                # Save the rd_challenge cookie if it was extracted
                if "rd_challenge" in cookies_dict:
                    logging.info(f"[COOKIES] Saving rd_challenge: {cookies_dict['rd_challenge'][:50]}...")
            else:
                logging.error("❌ Failed to handle challenge page in get_cookies.")
        
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

        # Add rd_challenge if it was extracted from challenge handling
        if challenge_url and "rd_challenge" in cookies_dict:
            cookies["rd_challenge"] = cookies_dict["rd_challenge"]

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

        # Build cookie string with rd_challenge if present
        cookie_parts = [
            "dpr=2",
            f'abra_csrf={self.cookies.get("abra_csrf")}',
            f'datr={self.cookies.get("datr")}',
            "ps_n=1",
            "ps_l=1"
        ]
        if "rd_challenge" in self.cookies:
            cookie_parts.append(f'rd_challenge={self.cookies.get("rd_challenge")}')
        
        headers = {
            "authority": "graph.meta.ai",
            "accept-language": "en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
            "cookie": "; ".join(cookie_parts),
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

    def generate_image_new(
        self,
        prompt: str,
        orientation: str = "VERTICAL",
        num_images: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate images using new API (based on captured network requests).
        
        Args:
            prompt: Text description of the image to generate
            orientation: Image orientation - "VERTICAL", "HORIZONTAL", or "SQUARE"
            num_images: Number of images to generate (default: 1)
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with response data and extracted image URLs
            
        Example:
            >>> ai = MetaAI(cookies={"datr": "...", "abra_sess": "..."})
            >>> result = ai.generate_image_new("Astronaut in space", orientation="VERTICAL")
            >>> if result.get('success'):
            >>>     for url in result.get('image_urls', []):
            >>>         print(f"Image URL: {url}")
        """
        try:
            response = self.generation_api.generate_image(
                prompt=prompt,
                orientation=orientation,
                num_images=num_images,
                **kwargs
            )
            
            # Extract image URLs
            image_urls = self.generation_api.extract_media_urls(response)
            
            return {
                "success": True,
                "prompt": prompt,
                "orientation": orientation,
                "num_images": num_images,
                "image_urls": image_urls,
                "response": response
            }
        except Exception as e:
            logging.error(f"Error generating images: {e}")
            return {
                "success": False,
                "error": str(e),
                "prompt": prompt
            }

    def generate_video_new(
        self,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate video using new API (based on captured network requests).
        
        Args:
            prompt: Text description of the video to generate
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with response data and extracted video URLs
            
        Example:
            >>> ai = MetaAI(cookies={"datr": "...", "abra_sess": "..."})
            >>> result = ai.generate_video_new("Astronaut in space")
            >>> if result.get('success'):
            >>>     for url in result.get('video_urls', []):
            >>>         print(f"Video URL: {url}")
        """
        try:
            response = self.generation_api.generate_video(
                prompt=prompt,
                **kwargs
            )
            
            # Extract video URLs
            video_urls = self.generation_api.extract_media_urls(response)
            
            return {
                "success": True,
                "prompt": prompt,
                "video_urls": video_urls,
                "response": response
            }
        except Exception as e:
            logging.error(f"Error generating video: {e}")
            return {
                "success": False,
                "error": str(e),
                "prompt": prompt
            }

    def generate_video(
        self,
        prompt: str,
        media_ids: Optional[list] = None,
        attachment_metadata: Optional[Dict[str, Any]] = None,
        orientation: Optional[str] = None,
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
            media_ids: Optional list of media IDs from uploaded images
            attachment_metadata: Optional dict with 'file_size' (int) and 'mime_type' (str)
            orientation: Video orientation. Valid values: "LANDSCAPE", "VERTICAL", "SQUARE". Defaults to None.
            wait_before_poll: Seconds to wait before starting to poll (default: 10)
            max_attempts: Maximum polling attempts (default: 30)
            wait_seconds: Seconds between polling attempts (default: 5)
            verbose: Whether to print status messages (default: True)

        Returns:
            Dictionary with success status, conversation_id, prompt, video_urls, and timestamp

        Example:
            ai = MetaAI(cookies={"datr": "...", "abra_sess": "..."})
            result = ai.generate_video(
                "Generate a video of a sunset",
                media_ids=["1234567890"],
                attachment_metadata={'file_size': 3310, 'mime_type': 'image/jpeg'}
            )
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
        
        # Try to use existing conversation if we have one
        conv_id = self.external_conversation_id if hasattr(self, 'external_conversation_id') else None
        
        return video_gen.generate_video(
            prompt=prompt,
            media_ids=media_ids,
            attachment_metadata=attachment_metadata,
            orientation=orientation,
            conversation_id=conv_id,
            wait_before_poll=wait_before_poll,
            max_attempts=max_attempts,
            wait_seconds=wait_seconds,
            verbose=verbose
        )

    def upload_image(self, file_path: str) -> Dict[str, Any]:
        """
        Upload an image to Meta AI for use in conversations, image generation, or video creation.
        
        Args:
            file_path: Path to the local image file to upload
            
        Returns:
            Dictionary containing:
                - success: bool - Whether the upload succeeded
                - media_id: str - The uploaded image's media ID (use this in prompts)
                - upload_session_id: str - Unique upload session ID
                - file_name: str - Original filename
                - file_size: int - File size in bytes
                - mime_type: str - MIME type of the image
                - error: str - Error message if upload failed
                
        Example:
            >>> ai = MetaAI(cookies={"datr": "...", "abra_sess": "..."})
            >>> result = ai.upload_image("path/to/image.jpg")
            >>> if result["success"]:
            >>>     print(f"Media ID: {result['media_id']}")
            >>>     # Use media_id in subsequent prompts for image analysis/generation
        """
        # Extract required tokens from cookies
        fb_dtsg = self.cookies.get("fb_dtsg", "")
        jazoest = self.cookies.get("jazoest", "")
        lsd = self.cookies.get("lsd", "")
        
        if not all([fb_dtsg, lsd]):
            return {
                "success": False,
                "error": "Missing required tokens (fb_dtsg, lsd). Please ensure cookies are properly set."
            }
        
        # Initialize uploader with session and cookies
        uploader = ImageUploader(self.session, self.cookies)
        
        # Perform upload
        result = uploader.upload_image(
            file_path=file_path,
            fb_dtsg=fb_dtsg,
            jazoest=jazoest,
            lsd=lsd
        )
        
        # Ensure we always return a dict
        if result is None:
            return {
                "success": False,
                "error": "Upload failed with no response"
            }
        
        return result


if __name__ == "__main__":
    meta = MetaAI()
    resp = meta.prompt("What was the Warriors score last game?", stream=False)
    print(resp)
