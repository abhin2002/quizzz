import datetime
import os
import requests
from typing import Optional
from fastapi.responses import JSONResponse

from fastapi import APIRouter, Body, File, Form, UploadFile

from quiz.schemas import ServiceInfo
from quiz.service import get_llm_service, get_quiz_prompt_generator

from .service import Transcriber
from pydantic import BaseModel
from config import settings

router = APIRouter()


transcripber = Transcriber()


@router.post('/transcriptions')
def transcribe(audio_file: bytes = File()) -> JSONResponse:
    """
    The function transcribes an audio file and returns the transcripts in a JSON response.
    """
    save_name = f'{datetime.datetime.now().strftime("%Y-%m-%d_%H%M-%S")}.mp3'
    with open(save_name, 'wb') as f:
        f.write(audio_file)

    try:
        transcripts = transcripber.transcribe(save_name)
    except Exception:
        return JSONResponse(content={'message': 'transcribe error'})

    os.remove(save_name)

    return JSONResponse(
        content={
            'message': 'success',
            'transcripts': transcripts,
        }
    )


@router.post('/transcriptions/from-url')
def transcribe_from_url(video_url: str = Form(...)) -> JSONResponse:
    """
    The function transcribes an audio/video file from a given S3 URL and returns the transcripts in a JSON response.
    """
    save_name = f'{datetime.datetime.now().strftime("%Y-%m-%d_%H%M-%S")}.mp4'  # Adjust extension as needed

    # Download the file from the provided URL
    try:
        response = requests.get(video_url, stream=True)
        response.raise_for_status()  # Raise an error for bad HTTP responses
        with open(save_name, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    except requests.RequestException as e:
        return JSONResponse(content={'message': f'Failed to download file from URL: {str(e)}'}, status_code=500)

    # Transcribe the downloaded file
    try:
        transcripts = transcripber.transcribe(save_name)
    except Exception as e:
        os.remove(save_name)  # Clean up the local file
        return JSONResponse(content={'message': f'Transcription error: {str(e)}'}, status_code=500)

    os.remove(save_name)  # Clean up the local file after transcription



    return JSONResponse(
        content={
            'message': 'success',
            'transcripts': transcripts,
        }
    )


# Hardcoded configuration
# QUIZ_CONFIG = {
#     'num_quizzes': 1,  # Exactly one question
#     'num_choices': 4   # Exactly 4 options per question
# }

DEFAULT_QUIZ_TYPE = 'multiple_choice'

router = APIRouter()

@router.post('/generate-quiz-from-url')
def transcribe_and_generate_quiz(
    video_url: str = Form(...),
    num_quizzes: Optional[int] = Form(1),  # Default to 1 question
    num_choices: Optional[int] = Form(4)  # Default to 4 choices per question
) -> JSONResponse:
    """
    This endpoint transcribes content from a given video URL and generates a multiple-choice quiz.
    """
    save_name = f'{datetime.datetime.now().strftime("%Y-%m-%d_%H%M-%S")}.mp4'  # Adjust extension as needed

    # Step 1: Download the file from the provided URL
    try:
        response = requests.get(video_url, stream=True)
        response.raise_for_status()  # Raise an error for bad HTTP responses
        with open(save_name, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    except requests.RequestException as e:
        return JSONResponse(content={'message': f'Failed to download file from URL: {str(e)}'}, status_code=500)

    # Step 2: Transcribe the downloaded file
    try:
        transcripts = transcripber.transcribe(save_name)
    except Exception as e:
        os.remove(save_name)  # Clean up the local file
        return JSONResponse(content={'message': f'Transcription error: {str(e)}'}, status_code=500)

    os.remove(save_name)  # Clean up the local file after transcription

    # Step 3: Generate quiz from the transcribed content
    service_info = ServiceInfo(service='OpenAIGPT', service_key=settings.GPT_KEY)  # Replace with your API key
    quiz_prompt_generator = get_quiz_prompt_generator(DEFAULT_QUIZ_TYPE)

    try:
        prompt = quiz_prompt_generator.generate_prompt(
            content=transcripts,
            num_quizzes=num_quizzes,
            num_choices=num_choices
        )
    except Exception as e:
        return JSONResponse(content={'message': f'Prompt generation error: {str(e)}'}, status_code=500)

    try:
        response = get_llm_service(service_info.service).call_service(service_info.service_key, prompt)
    except Exception as e:
        return JSONResponse(content={'message': f'LLM service call error: {str(e)}'}, status_code=500)

    return JSONResponse(
        content={
            'message': 'success',
            'transcripts': transcripts,
            'generated_quiz': response,
        }
    )


@router.post('/generate-quiz-from-transcript')
def generate_quiz_from_transcript(
    transcript: str = Form(...),
    num_quizzes: Optional[int] = Form(1),  # Default to 1 question
    num_choices: Optional[int] = Form(4)  # Default to 4 choices per question
) -> JSONResponse:
    """
    This endpoint generates a multiple-choice quiz directly from a provided transcript.
    """
    # Step 1: Generate quiz from the provided transcript
    service_info = ServiceInfo(service='OpenAIGPT', service_key=settings.GPT_KEY)  # Replace with your API key
    quiz_prompt_generator = get_quiz_prompt_generator(DEFAULT_QUIZ_TYPE)

    try:
        prompt = quiz_prompt_generator.generate_prompt(
            content=transcript,
            num_quizzes=num_quizzes,
            num_choices=num_choices
        )
    except Exception as e:
        return JSONResponse(content={'message': f'Prompt generation error: {str(e)}'}, status_code=500)

    try:
        response = get_llm_service(service_info.service).call_service(service_info.service_key, prompt)
    except Exception as e:
        return JSONResponse(content={'message': f'LLM service call error: {str(e)}'}, status_code=500)

    return JSONResponse(
        content={
            'message': 'success',
            'transcripts': transcript,
            'generated_quiz': response,
        }
    )



# class ServiceInfo(BaseModel):
#     service: str
#     service_key: str

# class QuizConfig(BaseModel):
#     num_quizzes: int
#     num_choices: int

# @router.post('/quizzes-from-transcription')
# def quizzes_from_transcription(
#     video_file: Optional[UploadFile] = File(None),
#     video_url: Optional[str] = Form(None),
#     service_info: ServiceInfo = Body(...),
#     quiz_type: str = Form("multiple_choice"),
#     quiz_config: QuizConfig = Body(...)
# ) -> JSONResponse:
#     """
#     Transcribes an audio/video file from upload or URL, generates a quiz based on transcription.
#     """
#     if not video_file and not video_url:
#         return JSONResponse(content={'message': 'Either video_file or video_url must be provided'}, status_code=400)

#     save_name = f'{datetime.datetime.now().strftime("%Y-%m-%d_%H%M-%S")}.mp4'  # Adjust file extension as needed

#     # Handle file upload
#     if video_file:
#         try:
#             with open(save_name, 'wb') as f:
#                 f.write(video_file.file.read())
#         except Exception as e:
#             return JSONResponse(content={'message': f'Failed to save uploaded file: {str(e)}'}, status_code=500)

#     # Handle URL input
#     elif video_url:
#         try:
#             response = requests.get(video_url, stream=True)
#             response.raise_for_status()  # Raise an error for bad HTTP responses
#             with open(save_name, 'wb') as f:
#                 for chunk in response.iter_content(chunk_size=8192):
#                     f.write(chunk)
#         except requests.RequestException as e:
#             return JSONResponse(content={'message': f'Failed to download file from URL: {str(e)}'}, status_code=500)

#     # Step 1: Transcription
#     try:
#         transcription = transcripber.transcribe(save_name)
#     except Exception as e:
#         os.remove(save_name)  # Clean up the local file
#         return JSONResponse(content={'message': f'Transcription error: {str(e)}'}, status_code=500)

#     os.remove(save_name)  # Clean up the local file after transcription

#     # Step 2: Quiz Generation
#     llm_service = get_llm_service(service_info.service)
#     quiz_prompt_generator = get_quiz_prompt_generator(quiz_type)

#     try:
#         prompt = quiz_prompt_generator.generate_prompt(content=transcription, **quiz_config.dict())
#     except Exception as e:
#         return JSONResponse(content={'message': f'Prompt generation error: {str(e)}'}, status_code=500)

#     try:
#         response = llm_service.call_service(service_info.service_key, prompt)
#     except Exception as e:
#         return JSONResponse(content={'message': f'LLM service call error: {str(e)}'}, status_code=500)

#     return JSONResponse(
#         content={
#             'message': 'success',
#             'generated_quiz': response,
#         }
#     )
