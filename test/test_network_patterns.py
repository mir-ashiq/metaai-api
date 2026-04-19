"""
Test suite for Meta AI API using mock network responses.
Tests SSE parsing, cookie handling, media extraction, and API patterns.
"""

import json
import logging
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typing import Dict, Any

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# FIXTURES: Mock Network Data
# ============================================================================

@pytest.fixture
def mock_sse_response():
    """Mock Server-Sent Events response from video generation."""
    return """data: {"type":"subscription_start"}
data: {"type":"message","data":{"xfb_kadabra_send_message":{"messages":{"edges":[{"node":{"content":{"imagine_video":{"videos":{"nodes":[{"mediaId":"917535734784048","video_url":"https://example.com/video1.mp4"}]}}}}}]}}}}
data: {"type":"done"}
"""


@pytest.fixture
def mock_video_generation_response():
    """Mock video generation GraphQL response."""
    return {
        "data": {
            "xfb_kadabra_send_message": {
                "messages": {
                    "edges": [
                        {
                            "node": {
                                "id": "msg_123",
                                "content": {
                                    "imagine_video": {
                                        "videos": {
                                            "nodes": [
                                                {
                                                    "mediaId": "917535734784048",
                                                    "video_url": "https://example.com/video1.mp4",
                                                    "videoDeliveryResponseResult": {
                                                        "progressive_urls": [
                                                            {"progressive_url": "https://example.com/video1_360p.mp4"}
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }
    }


@pytest.fixture
def mock_image_generation_response():
    """Mock image generation GraphQL response."""
    return {
        "data": {
            "xfb_imagine_send_message": {
                "messages": {
                    "edges": [
                        {
                            "node": {
                                "id": "msg_456",
                                "content": {
                                    "imagine_media": {
                                        "images": {
                                            "nodes": [
                                                {
                                                    "uri": "https://example.com/image1.jpg"
                                                },
                                                {
                                                    "uri": "https://example.com/image2.jpg"
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }
    }


@pytest.fixture
def mock_fetch_media_response():
    """Mock response from fetch media status."""
    return {
        "data": {
            "xfb_genai_fetch_post": {
                "messages": {
                    "edges": [
                        {
                            "node": {
                                "content": {
                                    "imagine_video": {
                                        "videos": {
                                            "nodes": [
                                                {
                                                    "mediaId": "917535734784048",
                                                    "uri": "https://example.com/video_ready.mp4",
                                                    "status": "READY"
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }
    }


@pytest.fixture
def mock_upload_response():
    """Mock image upload response."""
    return {
        "success": True,
        "media_id": "917535734784048",
        "upload_session_id": "12345-67890-abcdef",
        "file_name": "test_image.jpg",
        "file_size": 3310,
        "mime_type": "image/jpeg"
    }


# ============================================================================
# TESTS: Video Generation Module
# ============================================================================

class TestVideoGeneratorSSEParsing:
    """Test SSE response parsing for streaming video generation."""

    def test_parse_sse_response_valid(self, mock_sse_response):
        """Test parsing valid SSE formatted response."""
        from metaai_api.video_generation import VideoGenerator
        
        results = list(VideoGenerator.parse_sse_response(mock_sse_response))
        
        assert len(results) == 3
        assert results[0]["type"] == "subscription_start"
        assert results[1]["type"] == "message"
        assert results[2]["type"] == "done"
        
        # Verify message data structure
        assert "data" in results[1]
        assert "xfb_kadabra_send_message" in results[1]["data"]

    def test_parse_sse_response_empty(self):
        """Test parsing empty SSE response."""
        from metaai_api.video_generation import VideoGenerator
        
        results = list(VideoGenerator.parse_sse_response(""))
        assert len(results) == 0

    def test_parse_sse_response_invalid_json(self):
        """Test handling of invalid JSON in SSE response."""
        from metaai_api.video_generation import VideoGenerator
        
        invalid_sse = 'data: {invalid json}\ndata: {"valid": "json"}'
        results = list(VideoGenerator.parse_sse_response(invalid_sse))
        
        # Should skip invalid JSON and return valid ones
        assert len(results) == 1
        assert results[0]["valid"] == "json"


class TestVideoGeneratorMediaExtraction:
    """Test media ID extraction from video generation responses."""

    def test_extract_media_ids_from_response(self, mock_video_generation_response):
        """Test extracting media IDs from generation response."""
        from metaai_api.video_generation import VideoGenerator
        
        media_ids = VideoGenerator.extract_media_ids_from_response(mock_video_generation_response)
        
        assert len(media_ids) == 1
        assert "917535734784048" in media_ids

    def test_extract_video_urls_from_media(self, mock_video_generation_response):
        """Test extracting video URLs from media response."""
        from metaai_api.video_generation import VideoGenerator
        
        urls = VideoGenerator.extract_video_urls_from_media(mock_video_generation_response)
        
        assert len(urls) >= 1
        assert any(".mp4" in url for url in urls)
        assert "https://example.com/video1.mp4" in urls

    def test_extract_video_urls_progressive(self, mock_video_generation_response):
        """Test extracting progressive/alternate video URLs."""
        from metaai_api.video_generation import VideoGenerator
        
        urls = VideoGenerator.extract_video_urls_from_media(mock_video_generation_response)
        
        # Should contain both main and progressive URLs
        assert any("video1.mp4" in url for url in urls)
        assert any("360p" in url for url in urls)


class TestVideoGeneratorDocIds:
    """Test that correct doc_ids are defined for video operations."""

    def test_doc_ids_defined(self):
        """Test that all required doc_ids are defined."""
        from metaai_api.video_generation import VideoGenerator
        
        assert hasattr(VideoGenerator, 'VIDEO_CARD_DOC_ID')
        assert hasattr(VideoGenerator, 'VIDEO_GENERATE_DOC_ID')
        assert hasattr(VideoGenerator, 'VIDEO_FETCH_DOC_ID')
        
        assert VideoGenerator.VIDEO_CARD_DOC_ID == '666834feb70769370072c294c87ebd23'
        assert VideoGenerator.VIDEO_GENERATE_DOC_ID == 'a3d873304cb1411ba7f056e47060ad1d'
        assert VideoGenerator.VIDEO_FETCH_DOC_ID == '10b7bd5aa8b7537e573e49d701a5b21b'


# ============================================================================
# TESTS: Generation API
# ============================================================================

class TestGenerationAPIStatusQueries:
    """Test media status and fetch query methods."""

    def test_fetch_media_doc_id_defined(self):
        """Test that fetch media doc_id is defined."""
        from metaai_api.generation import GenerationAPI
        
        assert hasattr(GenerationAPI, 'FETCH_MEDIA_DOC_ID')
        assert GenerationAPI.FETCH_MEDIA_DOC_ID == '10b7bd5aa8b7537e573e49d701a5b21b'

    @patch('requests.Session.post')
    def test_fetch_media_status(self, mock_post, mock_fetch_media_response):
        """Test fetching media status by media ID."""
        from metaai_api.generation import GenerationAPI
        
        # Mock the response
        mock_response = Mock()
        mock_response.json.return_value = mock_fetch_media_response
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_post.return_value = mock_response
        
        api = GenerationAPI()
        result = api.fetch_media_status("917535734784048")
        
        assert result is not None
        assert isinstance(result, dict)
        mock_post.assert_called_once()

    def test_is_media_ready_with_urls(self, mock_fetch_media_response):
        """Test media readiness check when URLs are present."""
        from metaai_api.generation import GenerationAPI
        
        api = GenerationAPI()
        is_ready = api._is_media_ready(mock_fetch_media_response)
        
        assert is_ready is True

    def test_is_media_ready_without_data(self):
        """Test media readiness check with empty response."""
        from metaai_api.generation import GenerationAPI
        
        api = GenerationAPI()
        is_ready = api._is_media_ready({})
        
        assert is_ready is False

    def test_extract_media_urls_multipart_response(self, mock_fetch_media_response):
        """Test extracting URLs from fetch media response."""
        from metaai_api.generation import GenerationAPI
        
        api = GenerationAPI()
        urls = api.extract_media_urls(mock_fetch_media_response)
        
        assert len(urls) > 0
        assert any(".mp4" in url for url in urls)


class TestGenerationAPIResponseParsing:
    """Test response parsing for image and video generation."""

    def test_build_base_variables_text_to_video_matches_latest_capture(self):
        """TEXT_TO_VIDEO payload should follow current browser-captured variable shape."""
        from metaai_api.generation import GenerationAPI

        api = GenerationAPI()
        variables = api._build_base_variables(
            prompt="astronaut in space",
            operation="TEXT_TO_VIDEO",
            content_prefix="Animate",
        )

        imagine_request = variables["imagineOperationRequest"]

        assert imagine_request["operation"] == "TEXT_TO_VIDEO"
        assert imagine_request["textToImageParams"]["prompt"] == "astronaut in space"
        assert imagine_request["requestId"] is None
        assert variables["entryPoint"] == "KADABRA__UNKNOWN"
        assert variables["currentBranchPath"] == "0"

    def test_extract_image_urls(self, mock_image_generation_response):
        """Test extracting image URLs from response."""
        from metaai_api.generation import GenerationAPI
        
        api = GenerationAPI()
        urls = api.extract_media_urls(mock_image_generation_response)
        
        assert len(urls) == 2
        assert "https://example.com/image1.jpg" in urls
        assert "https://example.com/image2.jpg" in urls

    def test_extract_video_urls(self, mock_video_generation_response):
        """Test extracting video URLs from response."""
        from metaai_api.generation import GenerationAPI
        
        api = GenerationAPI()
        urls = api.extract_media_urls(mock_video_generation_response)
        
        assert len(urls) > 0
        assert any(".mp4" in url for url in urls)

    def test_parse_sse_response_surfaces_graphql_errors(self):
        """HTTP 200 with GraphQL errors should be marked as FAILED."""
        from metaai_api.generation import GenerationAPI

        api = GenerationAPI()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = (
            'data: {"errors":[{"message":"Cannot query field \\\"name\\\" on type \\\"User\\\".",' 
            '"extensions":{"code":"GRAPHQL_VALIDATION_FAILED"}}]}'
        )

        parsed = api._parse_sse_response(mock_response)

        assert parsed["has_graphql_errors"] is True
        assert parsed["streaming_state"] == "FAILED"
        assert len(parsed["graphql_errors"]) == 1
        assert parsed["graphql_errors"][0]["code"] == "GRAPHQL_VALIDATION_FAILED"

    @patch.dict("os.environ", {"META_AI_DOC_ID_TEXT_TO_IMAGE": "abc123override"}, clear=False)
    @patch("requests.Session.post")
    def test_generate_image_uses_doc_id_override(self, mock_post):
        """Environment override should be used for TEXT_TO_IMAGE doc_id payloads."""
        from metaai_api.generation import GenerationAPI

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/event-stream"}
        mock_response.text = (
            'data: {"data":{"sendMessageStream":{'
            '"streamingState":"OVERALL_DONE",'
            '"conversationId":"conv_1",'
            '"images":[{"id":"img_1","url":"https://example.com/image.jpg"}]'
            '}}}'
        )
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        api = GenerationAPI()
        result = api.generate_image("test image prompt")

        assert result["images"] == ["https://example.com/image.jpg"]
        sent_payload = mock_post.call_args.kwargs["json"]
        assert sent_payload["doc_id"] == "abc123override"


class TestMetaAIGenerationContracts:
    """Test strict success/error contract for generation wrappers."""

    def _build_ai_with_mock_generation(self) -> Any:
        from metaai_api.main import MetaAI

        ai = MetaAI.__new__(MetaAI)
        ai.generation_api = Mock()
        return ai

    def test_generate_image_new_fails_on_graphql_error(self):
        """Image wrapper must return success=False on GraphQL error events."""
        ai = self._build_ai_with_mock_generation()
        ai.generation_api.generate_image.return_value = {
            "images": [],
            "has_graphql_errors": True,
            "graphql_errors": [
                {
                    "message": "Cannot query field 'name' on type 'User'.",
                    "code": "GRAPHQL_VALIDATION_FAILED",
                }
            ],
            "events": [],
        }
        ai.generation_api.extract_media_urls.return_value = []

        result = ai.generate_image_new("a red apple")

        assert result["success"] is False
        assert result["status"] == "FAILED"
        assert result["has_graphql_errors"] is True
        assert "GRAPHQL_VALIDATION_FAILED" in result["error"]

    def test_generate_video_new_processing_without_media_is_not_success(self):
        """Strict semantics: no media output means success=False even while processing."""
        ai = self._build_ai_with_mock_generation()
        ai.generation_api.generate_video.return_value = {
            "conversation_id": "conv_123",
            "video_objects": [],
            "media_ids": [],
            "events": [],
            "has_graphql_errors": False,
            "graphql_errors": [],
        }
        ai.generation_api.fetch_video_urls_by_media_id = Mock(return_value=[])
        ai.generation_api.poll_for_video_ids = Mock(return_value=[])

        result = ai.generate_video_new("ocean waves", auto_poll=False)

        assert result["success"] is False
        assert result["status"] == "PROCESSING"
        assert result["processing"] is True
        assert result["has_graphql_errors"] is False

    def test_generate_video_new_fails_fast_on_graphql_errors(self):
        """GraphQL errors must fail and skip polling/fetch retries."""
        ai = self._build_ai_with_mock_generation()
        ai.generation_api.generate_video.return_value = {
            "conversation_id": "conv_err",
            "video_objects": [],
            "media_ids": [],
            "has_graphql_errors": True,
            "graphql_errors": [
                {
                    "message": "Cannot query field 'name' on type 'User'.",
                    "code": "GRAPHQL_VALIDATION_FAILED",
                }
            ],
            "events": [],
        }
        ai.generation_api.fetch_video_urls_by_media_id = Mock(return_value=[])
        ai.generation_api.poll_for_video_ids = Mock(return_value=[])

        result = ai.generate_video_new("a cat walking", auto_poll=True)

        assert result["success"] is False
        assert result["status"] == "FAILED"
        assert result["processing"] is False
        assert result["has_graphql_errors"] is True
        ai.generation_api.fetch_video_urls_by_media_id.assert_not_called()
        ai.generation_api.poll_for_video_ids.assert_not_called()

    def test_extend_video_fails_on_graphql_error(self):
        """Extend wrapper must propagate GraphQL failures with strict semantics."""
        ai = self._build_ai_with_mock_generation()
        ai.generation_api.extend_video.return_value = {
            "conversation_id": "conv_extend",
            "media_ids": [],
            "has_graphql_errors": True,
            "graphql_errors": [
                {
                    "message": "Persisted query mismatch",
                    "code": "GRAPHQL_VALIDATION_FAILED",
                }
            ],
            "events": [],
        }
        ai.generation_api.fetch_video_urls_by_media_id = Mock(return_value=[])

        result = ai.extend_video("123456", auto_poll=True)

        assert result["success"] is False
        assert result["status"] == "FAILED"
        assert result["has_graphql_errors"] is True
        ai.generation_api.fetch_video_urls_by_media_id.assert_not_called()


# ============================================================================
# TESTS: Chat Prompt Parsing and Fallbacks
# ============================================================================

class _FakeStreamingResponse:
    """Minimal response object for testing stream parsing paths."""

    def __init__(self, lines, status_code=200):
        self._lines = lines
        self.status_code = status_code
        self.headers = {"Content-Type": "text/event-stream"}
        self.text = "\n".join(lines)

    def iter_lines(self, decode_unicode=True):
        for line in self._lines:
            yield line

    def raise_for_status(self):
        return None

    def close(self):
        return None


class TestMetaAIChatPromptParsing:
    """Validate chat prompt parsing against modern and fallback response shapes."""

    def _build_ai_for_prompt_tests(self, post_side_effect):
        from metaai_api.main import MetaAI

        ai = MetaAI.__new__(MetaAI)
        ai.access_token = "ecto1:test-token"
        ai.cookies = {"datr": "test"}
        ai.external_conversation_id = None
        ai.offline_threading_id = None
        ai.session = Mock()
        ai.session.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }
        ai.session.post = Mock(side_effect=post_side_effect)
        ai.get_cookie_header = Mock(return_value="datr=test")
        ai.extract_access_token_from_page = Mock(return_value="ecto1:test-token")
        ai._check_response_for_auth_error = Mock(return_value=False)
        return ai

    @patch.dict("os.environ", {"META_AI_CHAT_DOC_ID": "doc-primary", "META_AI_CHAT_DOC_ID_ALT": "doc-alt"}, clear=False)
    def test_prompt_falls_back_to_alt_doc_id_when_primary_has_no_content(self):
        """If primary doc_id yields no text, prompt should retry with configured fallback doc_id."""
        ai = self._build_ai_for_prompt_tests(
            [
                _FakeStreamingResponse(
                    [
                        'data: {"data":{"sendMessageStream":{"conversationId":"conv-empty"}}}',
                    ]
                ),
                _FakeStreamingResponse(
                    [
                        'data: {"data":{"sendMessageStream":{"conversationId":"conv-ok","content":"Hello from fallback"}}}',
                    ]
                ),
            ]
        )

        result = ai.prompt("hello", stream=False, new_conversation=True)

        assert result["message"] == "Hello from fallback"
        assert ai.external_conversation_id == "conv-ok"
        first_payload = ai.session.post.call_args_list[0].kwargs["json"]
        second_payload = ai.session.post.call_args_list[1].kwargs["json"]
        assert first_payload["doc_id"] == "doc-primary"
        assert second_payload["doc_id"] == "doc-alt"

    @patch.dict("os.environ", {"META_AI_CHAT_DOC_ID": "doc-primary", "META_AI_CHAT_DOC_ID_ALT": "doc-alt"}, clear=False)
    def test_prompt_parses_plain_json_chat_message_shape(self):
        """Parser should accept non-SSE JSON lines returned by some chat doc_id variants."""
        ai = self._build_ai_for_prompt_tests(
            [
                _FakeStreamingResponse(
                    [
                        '{"data":{"message":{"conversationId":"conv-json","text":"Plain JSON chat response"}}}',
                    ]
                )
            ]
        )

        result = ai.prompt("hello", stream=False, new_conversation=True)

        assert result["message"] == "Plain JSON chat response"
        assert ai.external_conversation_id == "conv-json"

    @patch.dict("os.environ", {}, clear=True)
    def test_prompt_uses_unified_fallback_when_legacy_doc_id_fails(self):
        """Without env overrides, prompt should fall back from legacy chat doc_id to unified fallback."""
        ai = self._build_ai_for_prompt_tests(
            [
                _FakeStreamingResponse(
                    [
                        'data: {"errors":[{"message":"Cannot query field \'name\' on type \'User\'.","extensions":{"code":"GRAPHQL_VALIDATION_FAILED"}}]}',
                    ]
                ),
                _FakeStreamingResponse(
                    [
                        'data: {"data":{"sendMessageStream":{"conversationId":"conv-unified","content":"Fallback worked"}}}',
                    ]
                ),
            ]
        )

        result = ai.prompt("hello", stream=False, new_conversation=True)

        assert result["message"] == "Fallback worked"
        first_payload = ai.session.post.call_args_list[0].kwargs["json"]
        second_payload = ai.session.post.call_args_list[1].kwargs["json"]
        assert first_payload["doc_id"] == "ac0bad4b9787a393e160fb39f43404c1"
        assert second_payload["doc_id"] == "2f707e4a86f4b01adba97e1376cbdc14"

    @patch.dict("os.environ", {"META_AI_CHAT_DOC_ID": "doc-primary", "META_AI_CHAT_DOC_ID_ALT": "doc-alt"}, clear=False)
    def test_prompt_surfaces_graphql_validation_errors(self):
        """GraphQL validation failures in 200 responses should raise explicit errors."""

        def _error_response(*args, **kwargs):  # noqa: ANN002, ANN003
            return _FakeStreamingResponse(
                [
                    'data: {"errors":[{"message":"Cannot query field \'name\' on type \'User\'.","extensions":{"code":"GRAPHQL_VALIDATION_FAILED"}}]}',
                ]
            )

        ai = self._build_ai_for_prompt_tests(_error_response)

        with pytest.raises(Exception) as exc:
            ai.prompt("hello", stream=False, new_conversation=True)

        assert "GRAPHQL_VALIDATION_FAILED" in str(exc.value)


# ============================================================================
# TESTS: Image Upload Module
# ============================================================================

class TestImageUploadResponseParsing:
    """Test image upload response parsing."""

    def test_extract_media_id_direct(self, mock_upload_response):
        """Test extracting media_id from direct response field."""
        from metaai_api.image_upload import ImageUploader
        
        media_id = ImageUploader.extract_media_id_from_response(mock_upload_response)
        
        assert media_id == "917535734784048"

    def test_extract_media_id_nested(self):
        """Test extracting media_id from nested response structures."""
        from metaai_api.image_upload import ImageUploader
        
        nested_response = {
            "result": {
                "upload": {
                    "mediaId": "987654321"
                }
            }
        }
        
        media_id = ImageUploader.extract_media_id_from_response(nested_response)
        
        assert media_id == "987654321"

    def test_parse_upload_response_json(self, mock_upload_response):
        """Test parsing JSON upload response."""
        from metaai_api.image_upload import ImageUploader
        
        json_str = json.dumps(mock_upload_response)
        parsed = ImageUploader.parse_upload_response(json_str)
        
        assert parsed["media_id"] == "917535734784048"
        assert parsed["file_size"] == 3310

    def test_parse_upload_response_invalid(self):
        """Test parsing invalid response."""
        from metaai_api.image_upload import ImageUploader
        
        result = ImageUploader.parse_upload_response("invalid json")
        
        assert isinstance(result, dict)


# ============================================================================
# TESTS: Cookie Management (MetaAI Class)
# ============================================================================

class TestMetaAICookieHandling:
    """Test cookie loading from .env and environment."""

    @patch.dict('os.environ', {
        'META_AI_DATR': 'test_datr',
        'META_AI_ABRA_SESS': 'test_abra_sess',
        'META_AI_DPR': '1.25'
    })
    def test_load_cookies_from_env(self):
        """Test loading cookies from environment variables."""
        from metaai_api.main import MetaAI
        
        api = MetaAI()
        cookies = api.get_cookies_dict()
        
        assert 'datr' in cookies
        assert cookies['datr'] == 'test_datr'
        assert 'abra_sess' in cookies
        assert cookies['abra_sess'] == 'test_abra_sess'
        assert cookies.get('dpr') == '1.25'

    def test_get_cookie_header(self):
        """Test generating cookie header string."""
        from metaai_api.main import MetaAI
        
        test_cookies = {
            'datr': 'test_datr',
            'abra_sess': 'test_abra_sess'
        }
        
        # Create instance with provided cookies
        with patch.dict('os.environ', {}, clear=True):
            api = MetaAI(cookies=test_cookies)
        
        header = api.get_cookie_header()
        
        assert 'datr=test_datr' in header
        assert 'abra_sess=test_abra_sess' in header
        assert '; ' in header  # Multiple cookies separated


# ============================================================================
# TESTS: Client Module
# ============================================================================

class TestClientAnimateRequest:
    """Test client module animate request handling."""

    @patch('requests.post')
    def test_send_animate_request_with_tokens(self, mock_post):
        """Test sending animate request with provided tokens."""
        from metaai_api.client import send_animate_request
        
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response
        
        cookie_header = "datr=test; abra_sess=test"
        result = send_animate_request(
            cookie_header,
            "test prompt",
            fb_dtsg="test_dtsg",
            lsd="test_lsd"
        )
        
        assert result["success"] is True
        mock_post.assert_called_once()
        
        # Verify tokens were used
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["params"]["fb_dtsg"] == "test_dtsg"
        assert call_kwargs["params"]["lsd"] == "test_lsd"

    @patch('requests.post')
    def test_send_animate_request_with_fallback_tokens(self, mock_post):
        """Test fallback to default tokens if not provided."""
        from metaai_api.client import send_animate_request
        
        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response
        
        cookie_header = "datr=test; abra_sess=test"
        result = send_animate_request(cookie_header, "test prompt")
        
        # Should use default tokens
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["params"]["fb_dtsg"] is not None
        assert call_kwargs["params"]["lsd"] is not None


# ============================================================================
# TESTS: Integration
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple components."""

    def test_sse_to_media_extraction_flow(self, mock_sse_response):
        """Test complete flow from SSE response to media extraction."""
        from metaai_api.video_generation import VideoGenerator
        
        # Parse SSE response
        sse_data = list(VideoGenerator.parse_sse_response(mock_sse_response))
        
        # Should have message with data
        message = sse_data[1]
        assert "data" in message
        
        # Extract media IDs
        media_ids = VideoGenerator.extract_media_ids_from_response(message["data"])
        assert len(media_ids) > 0

    def test_response_parsing_pipeline(self, mock_video_generation_response):
        """Test complete response parsing pipeline."""
        from metaai_api.generation import GenerationAPI
        
        api = GenerationAPI()
        
        # Extract URLs
        urls = api.extract_media_urls(mock_video_generation_response)
        assert len(urls) > 0
        
        # Check readiness
        is_ready = api._is_media_ready(mock_video_generation_response)
        assert is_ready is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
