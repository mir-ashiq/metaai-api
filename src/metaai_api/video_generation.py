"""
Meta AI Video Generation Module
Advanced video generation and retrieval using Meta AI's GraphQL API
"""

import requests
import json
import time
import uuid
from typing import Dict, List, Optional, Any
from requests_html import HTMLSession
from metaai_api.utils import extract_value


class VideoGenerator:
    """
    A class to handle video generation requests to Meta AI's GraphQL API.
    Supports creating videos from text prompts and retrieving video URLs.
    """

    GRAPHQL_URL = 'https://www.meta.ai/api/graphql/'

    def __init__(
        self,
        cookies_str: Optional[str] = None,
        cookies_dict: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the VideoGenerator.
        Automatically fetches lsd and fb_dtsg tokens from Meta AI.

        Args:
            cookies_str: Cookie string in format "key=value; key=value"
            cookies_dict: Pre-parsed cookies dictionary
        """
        if cookies_dict:
            self.cookies = cookies_dict
            self.cookies_str = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
        elif cookies_str:
            self.cookies = self._parse_cookies(cookies_str)
            self.cookies_str = cookies_str
        else:
            raise ValueError("Either cookies_str or cookies_dict must be provided")

        # Always auto-fetch tokens
        try:
            tokens = self.get_lsd_and_dtsg(self.cookies_str)
            self.lsd = tokens['lsd']
            self.fb_dtsg = tokens['fb_dtsg']
        except Exception as e:
            raise ValueError(f"Failed to auto-fetch tokens: {e}")

    @staticmethod
    def _parse_cookies(cookie_str: str) -> Dict[str, str]:
        """Parse cookie string into dictionary"""
        cookies = {}
        for item in cookie_str.split('; '):
            if '=' in item:
                key, value = item.split('=', 1)
                cookies[key] = value
        return cookies

    @staticmethod
    def get_lsd_and_dtsg(cookies_str: str) -> Dict[str, str]:
        """
        Extract lsd and fb_dtsg from Meta AI page using provided cookies.
        
        Args:
            cookies_str: Cookie string in format "key1=value1; key2=value2; ..."
        
        Returns:
            Dictionary with 'lsd' and 'fb_dtsg' keys
        """
        # Fetch Meta AI page with cookies
        session = HTMLSession()
        headers = {"cookie": cookies_str}
        response = session.get("https://www.meta.ai/", headers=headers)
        
        # Extract lsd and fb_dtsg
        lsd = extract_value(response.text, start_str='"LSD",[],{"token":"', end_str='"')
        fb_dtsg = extract_value(response.text, start_str='DTSGInitData",[],{"token":"', end_str='"')
        
        return {
            "lsd": lsd,
            "fb_dtsg": fb_dtsg
        }

    @classmethod
    def quick_generate(
        cls,
        cookies_str: str,
        prompt: str,
        media_ids: Optional[List[str]] = None,
        attachment_metadata: Optional[Dict[str, Any]] = None,
        verbose: bool = True
    ) -> Dict:
        """
        Convenience method to generate a video with minimal setup.
        Automatically fetches tokens and generates video in one call.
        
        Args:
            cookies_str: Cookie string in format "key1=value1; key2=value2; ..."
            prompt: Text prompt for video generation
            media_ids: Optional list of media IDs from uploaded images
            attachment_metadata: Optional dict with 'file_size' (int) and 'mime_type' (str)
            verbose: Whether to print status messages
        
        Returns:
            Dictionary with success status, conversation_id, prompt, video_urls, and timestamp
        
        Example:
            result = VideoGenerator.quick_generate(
                cookies_str="datr=...; abra_sess=...",
                prompt="Generate a video of a sunset",
                media_ids=["1234567890"],
                attachment_metadata={'file_size': 3310, 'mime_type': 'image/jpeg'}
            )
        """
        generator = cls(cookies_str=cookies_str)
        return generator.generate_video(prompt=prompt, media_ids=media_ids, attachment_metadata=attachment_metadata, verbose=verbose)

    def build_headers(
        self,
        content_type: str = 'application/x-www-form-urlencoded',
        friendly_name: Optional[str] = None,
        additional_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Build dynamic headers for Meta AI API requests.

        Args:
            content_type: Content-Type header value
            friendly_name: Optional X-FB-Friendly-Name for the request
            additional_headers: Optional dict of additional headers to merge

        Returns:
            Complete headers dictionary
        """
        # Base headers common to all requests
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.5',
            'content-type': content_type,
            'origin': 'https://www.meta.ai',
            'referer': 'https://www.meta.ai/',
            'sec-ch-ua': '"Brave";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'x-asbd-id': '359341',
            'x-fb-lsd': self.lsd,
        }

        # Add optional friendly name
        if friendly_name:
            headers['x-fb-friendly-name'] = friendly_name

        # Add additional headers specific to request type
        if additional_headers:
            headers.update(additional_headers)

        return headers

    def create_video_generation_request(
        self,
        prompt_text: str,
        media_ids: Optional[List[str]] = None,
        attachment_metadata: Optional[Dict[str, Any]] = None,
        verbose: bool = True
    ) -> Optional[str]:
        """
        Send video generation request to Meta AI using raw multipart body.

        Args:
            prompt_text: The text prompt for video generation
            media_ids: Optional list of media IDs from uploaded images
            attachment_metadata: Optional dict with 'file_size' (int) and 'mime_type' (str)
            verbose: Whether to print status messages

        Returns:
            external_conversation_id if successful, None otherwise
        """
        # Generate unique IDs
        external_conversation_id = str(uuid.uuid4())
        offline_threading_id = str(int(time.time() * 1000000000))[:19]
        thread_session_id = str(uuid.uuid4())
        bot_offline_threading_id = str(int(time.time() * 1000000000) + 1)[:19]
        qpl_join_id = str(uuid.uuid4()).replace('-', '')

        # Build headers with multipart-specific additions
        multipart_headers = {
            'priority': 'u=1, i',
            'sec-ch-ua-full-version-list': '"Brave";v="141.0.0.0", "Not?A_Brand";v="8.0.0.0", "Chromium";v="141.0.0.0"',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform-version': '"19.0.0"',
            'sec-gpc': '1',
        }

        headers = self.build_headers(
            content_type='multipart/form-data; boundary=----WebKitFormBoundaryu59CeaZS4ag939lz',
            additional_headers=multipart_headers
        )

        # Build variables JSON (compact, no extra spaces)
        variables = json.dumps({
            "message": {"sensitive_string_value": prompt_text},
            "externalConversationId": external_conversation_id,
            "offlineThreadingId": offline_threading_id,
            "threadSessionId": thread_session_id,
            "isNewConversation": True,
            "suggestedPromptIndex": None,
            "promptPrefix": None,
            "entrypoint": "KADABRA__CHAT__UNIFIED_INPUT_BAR",
            "attachments": [],
            "attachmentsV2": media_ids if media_ids else [],
            "activeMediaSets": [],
            "activeCardVersions": [],
            "activeArtifactVersion": None,
            "userUploadEditModeInput": None,
            "reelComposeInput": None,
            "qplJoinId": qpl_join_id,
            "sourceRemixPostId": None,
            "gkPlannerOrReasoningEnabled": True,
            "selectedModel": "BASIC_OPTION",
            "conversationMode": None,
            "selectedAgentType": "PLANNER",
            "conversationStarterId": None,
            "promptType": None,
            "artifactRewriteOptions": None,
            "imagineOperationRequest": None,
            "imagineClientOptions": {"orientation": "VERTICAL"},
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
                "external_conversation_id": external_conversation_id,
                "is_new_conversation": True,
                "meta_ai_entry_point": "KADABRA__CHAT__UNIFIED_INPUT_BAR",
                "offline_threading_id": offline_threading_id,
                "prompt_id": None,
                "prompt_session_id": thread_session_id
            },
            "alakazam_enabled": True,
            "skipInFlightMessageWithParams": None,
            "__relay_internal__pv__KadabraSocialSearchEnabledrelayprovider": False,
            "__relay_internal__pv__KadabraZeitgeistEnabledrelayprovider": False,
            "__relay_internal__pv__alakazam_enabledrelayprovider": True,
            "__relay_internal__pv__sp_kadabra_survey_invitationrelayprovider": True,
            "__relay_internal__pv__KadabraAINativeUXrelayprovider": False,
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
            "__relay_internal__pv__kadabra_reels_connect_featuresrelayprovider": False,
            "__relay_internal__pv__AbraBugNubrelayprovider": False,
            "__relay_internal__pv__AbraRedteamingrelayprovider": False,
            "__relay_internal__pv__AbraDebugDevOnlyrelayprovider": False,
            "__relay_internal__pv__kadabra_enable_open_in_editor_message_actionrelayprovider": True,
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
            "__relay_internal__pv__AbraIsLoggedOutrelayprovider": False,
            "__relay_internal__pv__KadabraCanvasDisplayHeaderV2relayprovider": False,
            "__relay_internal__pv__AbraArtifactEditorDebugModerelayprovider": False,
            "__relay_internal__pv__AbraArtifactEditorDownloadHTMLEnabledrelayprovider": False,
            "__relay_internal__pv__kadabra_create_row_hover_optionsrelayprovider": False,
            "__relay_internal__pv__kadabra_media_info_pillsrelayprovider": True,
            "__relay_internal__pv__KadabraConcordInternalProfileBadgeEnabledrelayprovider": False,
            "__relay_internal__pv__KadabraSocialGraphrelayprovider": True
        }, separators=(',', ':'))

        print(variables)

        # Build raw multipart body (exactly as in working example)
        spin_t = str(int(time.time()))
        body = f"""------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="av"\r
\r
813590375178585\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="__user"\r
\r
0\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="__a"\r
\r
1\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="__req"\r
\r
q\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="__hs"\r
\r
20413.HYP:kadabra_pkg.2.1...0\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="dpr"\r
\r
1\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="__ccg"\r
\r
GOOD\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="__rev"\r
\r
1030219547\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="__s"\r
\r
q59jx4:9bnqdw:3ats33\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="__hsi"\r
\r
7575127759957881428\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="__dyn"\r
\r
7xeUjG1mxu1syUqxemh0no6u5U4e2C1vzEdE98K360CEbo1nEhw2nVEtwMw6ywaq221FwpUO0n24oaEnxO0Bo7O2l0Fwqo31w9O1lwlE-U2zxe2GewbS361qw82dUlwhE-15wmo423-0j52oS0Io5d0bS1LBwNwKG0WE8oC1IwGw-wlUcE2-G2O7E5y1rwa211wo84y1iwfe1aw\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="__csr"\r
\r
gaJNBjWsAJvliQPqlWFFknAiUB2bBjWLmhyblepaGyVFGy8y2i5pEW68mwwwPwxgtNgv2AMEu6PAgrCwc7F212xxe5YyVC1pAg01sq99uQ1zK0dp75gKzAy8y0EjcgQ8Ek0yMJC6G1og5KrXD4GexS8wdasU8U1e4075UeEuwfCA8K0hWiU2tAyE5m0gm0Jo0xUGxh1veU0gGyWfe0iK1xo32yXhoKkw56pwMw1e25onU4i0TA0xaxu00B1Q2ha2K3V0eqCmawnEgg2Gw\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="__hsdp"\r
\r
gdDdNhMlJ8bNG7i42aHgWzckH57ylAt8NkkOGCVQ8Ay8myETxW1vh48gHx-UC9Bgpy87G0BUfU7i0JFUeo7Cm12wlo5OawRwDwzxW1zg33wgodU\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="__hblp"\r
\r
08W5EWt0BzUWp5Q4vz4HOk5kVogDGqmHgyi8xq9gNrxG1vh8B2K6pry4mVk8x28wuE5a1DxO1Qwr84Cu3C1VBwCxK2W2qi2y1LwDwzyK445Gwi63-0wUkxa9AyEjgogy3-\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="__sjsp"\r
\r
gdDtsAFMlJ8bNG7i47AG5lxmUmDiFQca9U\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="__comet_req"\r
\r
72\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="fb_dtsg"\r
\r
{self.fb_dtsg}\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="jazoest"\r
\r
25499\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="lsd"\r
\r
{self.lsd}\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="__spin_r"\r
\r
1030219547\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="__spin_b"\r
\r
trunk\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="__spin_t"\r
\r
{spin_t}\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="__jssesw"\r
\r
1\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="__crn"\r
\r
comet.kadabra.KadabraAssistantRoute\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="fb_api_caller_class"\r
\r
RelayModern\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="fb_api_req_friendly_name"\r
\r
useKadabraSendMessageMutation\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="server_timestamps"\r
\r
true\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="variables"\r
\r
{variables}\r
------WebKitFormBoundaryu59CeaZS4ag939lz\r
Content-Disposition: form-data; name="doc_id"\r
\r
25290947477183545\r
------WebKitFormBoundaryu59CeaZS4ag939lz--\r
"""

        # URL with query parameters
        url = f"{self.GRAPHQL_URL}?fb_dtsg={self.fb_dtsg}&jazoest=25499&lsd={self.lsd}"

        try:
            response = requests.post(
                url,
                cookies=self.cookies,
                headers=headers,
                data=body.encode('utf-8'),
                timeout=30
            )

            if response.status_code == 200:
                return external_conversation_id
            else:
                return None

        except Exception as e:
            return None

    def fetch_video_urls(
        self,
        conversation_id: str,
        max_attempts: int = 30,
        wait_seconds: int = 5,
        verbose: bool = True
    ) -> List[str]:
        """
        Poll for video URLs from a conversation.

        Args:
            conversation_id: The conversation ID to fetch videos from
            max_attempts: Maximum number of polling attempts
            wait_seconds: Seconds to wait between attempts
            verbose: Whether to print status messages

        Returns:
            List of video URLs
        """
        # Build headers with query-specific friendly name
        headers = self.build_headers(
            content_type='application/x-www-form-urlencoded',
            friendly_name='KadabraPromptRootQuery'
        )

        # Build variables
        variables = {
            "prompt_id": conversation_id,
            "__relay_internal__pv__kadabra_voice_consumptionrelayprovider": False,
            "__relay_internal__pv__AbraIsLoggedOutrelayprovider": False,
            "__relay_internal__pv__KadabraConversationRenamingrelayprovider": True,
            "__relay_internal__pv__KadabraSpacesEnabledrelayprovider": False,
            "__relay_internal__pv__KadabraRecipesEnabledrelayprovider": False,
            "__relay_internal__pv__KadabraFOASharingEnabledrelayprovider": True,
            "__relay_internal__pv__KadabraFeedImageDimensionrelayprovider": 800,
            "__relay_internal__pv__kadabra_story_builder_enabledrelayprovider": False,
            "__relay_internal__pv__kadabra_imagine_canvas_enable_dev_settingsrelayprovider": False,
            "__relay_internal__pv__enable_kadabra_partial_resultsrelayprovider": False,
            "__relay_internal__pv__kadabra_create_media_deletionrelayprovider": False,
            "__relay_internal__pv__kadabra_moodboardrelayprovider": False,
            "__relay_internal__pv__KadabraVideoDeliveryRequestrelayprovider": {
                "dash_manifest_requests": [{}],
                "progressive_url_requests": [{"quality": "HD"}, {"quality": "SD"}]
            },
            "__relay_internal__pv__AbraSearchInlineReferencesEnabledrelayprovider": True,
            "__relay_internal__pv__AbraComposedTextWidgetsrelayprovider": True,
            "__relay_internal__pv__KadabraNewCitationsEnabledrelayprovider": True,
            "__relay_internal__pv__WebPixelRatiorelayprovider": 1,
            "__relay_internal__pv__KadabraWidgetsRedesignEnabledrelayprovider": False,
            "__relay_internal__pv__AbraArtifactDragImagineFromConversationrelayprovider": True,
            "__relay_internal__pv__kadabra_media_item_renderer_heightrelayprovider": 545,
            "__relay_internal__pv__kadabra_media_item_renderer_widthrelayprovider": 620,
            "__relay_internal__pv__AbraBugNubrelayprovider": False,
            "__relay_internal__pv__AbraDebugDevOnlyrelayprovider": False,
            "__relay_internal__pv__abra_silverstone_enable_hidden_commentsrelayprovider": True,
            "__relay_internal__pv__kadabra_voicerelayprovider": True,
            "__relay_internal__pv__KadabraSocialSearchEnabledrelayprovider": False,
            "__relay_internal__pv__KadabraZeitgeistEnabledrelayprovider": False,
            "__relay_internal__pv__alakazam_enabledrelayprovider": True,
            "__relay_internal__pv__sp_kadabra_survey_invitationrelayprovider": True,
            "__relay_internal__pv__KadabraAINativeUXrelayprovider": False,
            "__relay_internal__pv__AbraArtifactsEnabledrelayprovider": True,
            "__relay_internal__pv__KadabraMemoryEnabledrelayprovider": False,
            "__relay_internal__pv__AbraPlannerEnabledrelayprovider": True,
            "__relay_internal__pv__AbraWidgetsEnabledrelayprovider": False,
            "__relay_internal__pv__KadabraDeepResearchEnabledrelayprovider": False,
            "__relay_internal__pv__KadabraThinkHarderEnabledrelayprovider": False,
            "__relay_internal__pv__KadabraVergeEnabledrelayprovider": False,
            "__relay_internal__pv__KadabraProductSearchEnabledrelayprovider": False,
            "__relay_internal__pv__KadabraAreServiceEnabledrelayprovider": False,
            "__relay_internal__pv__kadabra_render_reasoning_response_statesrelayprovider": True,
            "__relay_internal__pv__kadabra_reasoning_cotrelayprovider": False,
            "__relay_internal__pv__kadabra_enable_send_message_retryrelayprovider": True,
            "__relay_internal__pv__KadabraEmailCalendarIntegrationrelayprovider": False,
            "__relay_internal__pv__kadabra_reels_connect_featuresrelayprovider": False,
            "__relay_internal__pv__AbraRedteamingrelayprovider": False,
            "__relay_internal__pv__kadabra_enable_open_in_editor_message_actionrelayprovider": True,
            "__relay_internal__pv__AbraThreadsEnabledrelayprovider": False,
            "__relay_internal__pv__AbraQPDocUploadNuxTriggerNamerelayprovider": "meta_dot_ai_abra_web_doc_upload_nux_tour",
            "__relay_internal__pv__AbraSurfaceNuxIDrelayprovider": "12177"
        }

        # Build data payload
        data = {
            'av': '813590375178585',
            '__user': '0',
            '__a': '1',
            '__req': 's',
            '__hs': '20413.HYP:kadabra_pkg.2.1...0',
            'dpr': '1',
            '__ccg': 'GOOD',
            '__rev': '1030219547',
            '__s': 'q59jx4:9bnqdw:3ats33',
            '__hsi': '7575127759957881428',
            '__dyn': '7xeUjG1mxu1syUqxemh0no6u5U4e2C1vzEdE98K360CEbo1nEhw2nVEtwMw6ywaq221FwpUO0n24oaEnxO0Bo7O2l0Fwqo31w9O1lwlE-U2zxe2GewbS361qw82dUlwhE-15wmo423-0j52oS0Io5d0bS1LBwNwKG0WE8oC1IwGw-wlUcE2-G2O7E5y1rwa211wo84y1iwfe1aw',
            '__csr': 'gaJNBjWsAJvliQPqlWFFknAiUB2bBjWLmhyblepaGyVFGy8y2i5pEW68mwwwPwxgtNgv2AMEu6PAgrCwc7F212xxe5YyVC1pAg01sq99uQ1zK0dp75gKzAy8y0EjcgQ8Ek0yMJC6G1og5KrXD4GexS8wdasU8U1e4075UeEuwfCA8K0hWiU2tAyE5m0gm0Jo0xUGxh1veU0gGyWfe0iK1xo32yXhoKkw56pwMw1e25onU4i0TA0xaxu00B1Q2ha2K3V0eqCmawnEgg2Gw',
            '__hsdp': 'gdDdNhMlJ8bNG7i42aHgWzckH57ylAt8NkkOGCVQ8Ay8myETxW1vh48gHx-UC9Bgpy87G0BUfU7i0JFUeo7Cm12wlo5OawRwDwzxW1zg33wgodU',
            '__hblp': '08W5EWt0BzUWp5Q4vz4HOk5kVogDGqmHgyi8xq9gNrxG1vh8B2K6pry4mVk8x28wuE5a1DxO1Qwr84Cu3C1VBwCxK2W2qi2y1LwDwzyK445Gwi63-0wUkxa9AyEjgogy3-',
            '__sjsp': 'gdDtsAFMlJ8bNG7i47AG5lxmUmDiFQca9U',
            '__comet_req': '72',
            'fb_dtsg': self.fb_dtsg,
            'jazoest': '25499',
            'lsd': self.lsd,
            '__spin_r': '1030219547',
            '__spin_b': 'trunk',
            '__spin_t': str(int(time.time())),
            '__jssesw': '1',
            '__crn': 'comet.kadabra.KadabraAssistantRoute',
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'KadabraPromptRootQuery',
            'server_timestamps': 'true',
            'variables': json.dumps(variables),
            'doc_id': '25290569913909283',
        }

        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.post(
                    self.GRAPHQL_URL,
                    cookies=self.cookies,
                    headers=headers,
                    data=data,
                    timeout=30
                )

                if response.status_code == 200:
                    # Extract video URLs from response
                    video_urls = self._extract_video_urls_from_response(response.text)

                    if video_urls:
                        return video_urls
                    else:
                        time.sleep(wait_seconds)
                else:
                    time.sleep(wait_seconds)

            except Exception as e:
                time.sleep(wait_seconds)

        return []

    @staticmethod
    def _extract_video_urls_from_response(response_text: str) -> List[str]:
        """
        Extract video URLs from Meta AI GraphQL response.
        Uses the CORRECT structure from the original GitHub repo.

        Args:
            response_text: The response text to extract URLs from

        Returns:
            List of video URLs
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("[VIDEO URL EXTRACTION] Starting extraction with proper structure...")
        logger.debug(f"[VIDEO URL EXTRACTION] Response length: {len(response_text)} characters")

        urls: List[str] = []

        try:
            # Parse the response
            data = json.loads(response_text)
            logger.info("[VIDEO URL EXTRACTION] Successfully parsed response as JSON")
            
            # CORRECT STRUCTURE from original GitHub code:
            # data -> xfb_genai_fetch_post (or xab_abra__xfb_genai_fetch_post)
            # -> messages -> edges -> node -> content -> imagine_video
            
            data_obj = data.get("data", {})
            fetch_post = data_obj.get("xfb_genai_fetch_post") or data_obj.get("xab_abra__xfb_genai_fetch_post") or {}
            
            if not fetch_post:
                logger.warning("[VIDEO URL EXTRACTION] No xfb_genai_fetch_post or xab_abra__xfb_genai_fetch_post found in response")
            else:
                logger.info(f"[VIDEO URL EXTRACTION] Found fetch_post: {list(fetch_post.keys())}")

            messages = fetch_post.get("messages", {}).get("edges", [])
            logger.info(f"[VIDEO URL EXTRACTION] Found {len(messages)} message edges")
            
            for edge_idx, edge in enumerate(messages):
                node = edge.get("node", {})
                content = node.get("content", {})
                imagine_video = content.get("imagine_video") or {}
                
                if not imagine_video:
                    logger.debug(f"[VIDEO URL EXTRACTION] Edge {edge_idx}: No imagine_video found")
                    continue
                
                logger.info(f"[VIDEO URL EXTRACTION] Edge {edge_idx}: Found imagine_video with keys: {list(imagine_video.keys())}")

                # Extract from videos.nodes[] array
                videos = imagine_video.get("videos", {}).get("nodes", [])
                logger.info(f"[VIDEO URL EXTRACTION] Edge {edge_idx}: Found {len(videos)} video nodes")
                
                for video_idx, video in enumerate(videos):
                    # Try video_url or uri
                    uri = video.get("video_url") or video.get("uri")
                    if uri:
                        logger.info(f"[VIDEO URL EXTRACTION] Found video_url/uri in videos.nodes[{video_idx}]: {uri[:100]}...")
                        urls.append(uri)
                    
                    # Try videoDeliveryResponseResult.progressive_urls[]
                    delivery = video.get("videoDeliveryResponseResult") or {}
                    prog = delivery.get("progressive_urls", [])
                    logger.info(f"[VIDEO URL EXTRACTION] Found {len(prog)} progressive_urls in video {video_idx}")
                    
                    for prog_idx, p in enumerate(prog):
                        pu = p.get("progressive_url")
                        if pu:
                            logger.info(f"[VIDEO URL EXTRACTION] Found progressive_url[{prog_idx}]: {pu[:100]}...")
                            urls.append(pu)

                # Extract from single video object
                single_video = imagine_video.get("video") or {}
                if isinstance(single_video, dict) and single_video:
                    logger.info(f"[VIDEO URL EXTRACTION] Found single video object with keys: {list(single_video.keys())}")
                    
                    uri = single_video.get("video_url") or single_video.get("uri")
                    if uri:
                        logger.info(f"[VIDEO URL EXTRACTION] Found video_url/uri in single video: {uri[:100]}...")
                        urls.append(uri)
                    
                    delivery = single_video.get("videoDeliveryResponseResult") or {}
                    prog = delivery.get("progressive_urls", [])
                    logger.info(f"[VIDEO URL EXTRACTION] Found {len(prog)} progressive_urls in single video")
                    
                    for prog_idx, p in enumerate(prog):
                        pu = p.get("progressive_url")
                        if pu:
                            logger.info(f"[VIDEO URL EXTRACTION] Found progressive_url[{prog_idx}]: {pu[:100]}...")
                            urls.append(pu)

        except json.JSONDecodeError as e:
            logger.error(f"[VIDEO URL EXTRACTION] JSON decode failed: {e}")
            logger.debug(f"[VIDEO URL EXTRACTION] Response preview: {response_text[:500]}")
            
            # Fallback to regex
            logger.info("[VIDEO URL EXTRACTION] Falling back to regex extraction...")
            import re
            urls = re.findall(r'https?://[^\s"\'<>]+fbcdn[^\s"\'<>]+\.mp4[^\s"\'<>]*', response_text)
            logger.info(f"[VIDEO URL EXTRACTION] Regex found {len(urls)} .mp4 URLs")

        # Deduplicate while preserving order
        seen = set()
        unique_urls: List[str] = []
        for u in urls:
            if u and u not in seen:
                seen.add(u)
                unique_urls.append(u)
        
        logger.info(f"[VIDEO URL EXTRACTION] Final result: {len(unique_urls)} unique video URLs")
        if unique_urls:
            for idx, url in enumerate(unique_urls, 1):
                logger.info(f"[VIDEO URL EXTRACTION] Final URL {idx}: {url[:150]}...")
        else:
            logger.warning("[VIDEO URL EXTRACTION] ⚠️ NO VIDEO URLs FOUND!")
            logger.debug(f"[VIDEO URL EXTRACTION] Response preview (first 1000 chars): {response_text[:1000]}")
        
        return unique_urls

    def generate_video(
        self,
        prompt: str,
        media_ids: Optional[List[str]] = None,
        attachment_metadata: Optional[Dict[str, Any]] = None,
        wait_before_poll: int = 10,
        max_attempts: int = 30,
        wait_seconds: int = 5,
        verbose: bool = True
    ) -> Dict:
        """
        Main function to generate video and retrieve URLs.

        Args:
            prompt: Text prompt for video generation
            media_ids: Optional list of media IDs from uploaded images
            attachment_metadata: Optional dict with 'file_size' (int) and 'mime_type' (str)
            wait_before_poll: Seconds to wait before starting to poll
            max_attempts: Maximum polling attempts
            wait_seconds: Seconds between polling attempts
            verbose: Whether to print status messages

        Returns:
            Dictionary with success status, conversation_id, prompt, video_urls, and timestamp
        """
        # Step 1: Create video generation request
        conversation_id = self.create_video_generation_request(
            prompt_text=prompt,
            media_ids=media_ids,
            attachment_metadata=attachment_metadata,
            verbose=verbose
        )

        if not conversation_id:
            return {"success": False, "error": "Failed to create video generation request"}

        # Step 2: Wait a bit before polling
        time.sleep(wait_before_poll)

        # Step 3: Poll for video URLs
        video_urls = self.fetch_video_urls(
            conversation_id=conversation_id,
            max_attempts=max_attempts,
            wait_seconds=wait_seconds,
            verbose=verbose
        )

        result = {
            "success": len(video_urls) > 0,
            "conversation_id": conversation_id,
            "prompt": prompt,
            "video_urls": video_urls,
            "timestamp": time.time()
        }

        return result
