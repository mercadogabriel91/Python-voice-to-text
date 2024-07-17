import speech_recognition as sr
import json
import os
import boto3
import speech_recognition as sr


def getS3File(file):
    bucket_name = "gaben-testing-bucket-delete"
    file_key = f"{file}.wav"
    s3 = boto3.client("s3")

    try:
        # Download the file from S3
        local_file_path = f"/tmp/{file}.wav"
        s3.download_file(bucket_name, file_key, local_file_path)

        return local_file_path  # Return the local file path

    except Exception as e:
        print(f"Error: {str(e)}")
        return None  # Return None if there's an error downloading the file


def deleteS3File(file):
    bucket_name = "gaben-testing-bucket-delete"
    file_key = f"{file}.wav"
    s3 = boto3.client("s3")

    try:
        # Delete the file from S3
        s3.delete_object(Bucket=bucket_name, Key=file_key)
        print(f"File {file} deleted from S3")
    except Exception as e:
        print(f"Error deleting file from S3: {str(e)}")


def processAudio(event, context):
    try:
        if "body" in event and "fileName" in event["body"]:
            body_data = json.loads(event["body"])
            fileName = body_data["fileName"]

            # Get the local file path from S3
            local_file_path = getS3File(fileName)

            if local_file_path:
                # Perform audio transcription
                recognizer = sr.Recognizer()

                # Load the audio file
                audio_file = sr.AudioFile(local_file_path)

                with audio_file as source:
                    # Adjust for ambient noise and record the audio
                    recognizer.adjust_for_ambient_noise(source)
                    audio = recognizer.record(source)

                    try:
                        # Use Google Web Speech API to transcribe the audio
                        text = recognizer.recognize_google(audio)
                        result = {"text": text}
                    except sr.UnknownValueError:
                        result = {
                            "error": "Speech Recognition could not understand audio"
                        }
                    except sr.RequestError as e:
                        result = {
                            "error": f"Could not request results from Google Web Speech API; {e}"
                        }

                # Clean up: Delete the local file
                os.remove(local_file_path)

                # Delete the file from S3
                deleteS3File(fileName)

                return {"statusCode": 200, "body": json.dumps(result)}
            else:
                return {
                    "statusCode": 500,
                    "body": json.dumps({"error": "Error downloading file from S3"}),
                }

        else:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid request format"}),
            }

    except Exception as e:
        print("BIG ASS ERROR")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Internal Server Error: {str(e)}"}),
        }
