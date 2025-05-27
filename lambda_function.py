import json
import configparser
import os
from db.worker import DBWorker
from bedrock.worker import BedrockWorker

def lambda_handler(event, context):
    config = configparser.ConfigParser()
    env = os.getenv('ENV', default='dev.ini')
    config.read(env)

    db_worker = DBWorker(
        config['mysql']['HOST'],
        config['mysql']['USER'],
        config['mysql']['PASSWORD'],
        config['mysql']['DATABASE'],
        True
    )

    bedrock_worker = BedrockWorker(
        config['aws']['AWS_BEDROCK_ACCESS_KEY'],
        config['aws']['AWS_BEDROCK_SECRET_KEY'],
        config['aws']['AWS_REGION'],
        config['aws']['BEDROCK_MODEL_ID']
    )

    for record in event['Records']:
        print(record)
        report_id = None 
        try:
            message_body = json.loads(record['body'])
            report_id = message_body.get("report_id")
            if not report_id:
                print("Report ID not found in the message.")
                continue
            report_data = db_worker.call_get_report_details(report_id)

            if not report_data:
                print(f"Report with ID {report_id} not found.")
                continue

            prompt = (
                "Analyze the following report and return the answer in a strictly valid JSON format. "
                "Your response must exactly follow the structure below without any additional text or commentary:\n\n"
                "{\n"
                '  "recommendation": "Provide detailed recommendations for the administration on how to resolve the issue. Include clear, step-by-step actions, resource allocation suggestions, and any necessary follow-up measures to address the problem effectively.",\n'
                '  "short_answer": "Provide a concise response to the user who submitted the report. For example: \'We have reviewed your report and will take appropriate action as soon as possible.\'. Include additional advice only if relevant and appropriate, without transferring the responsibility of fixing the issue onto the user.",\n'
                '  "offisial_summary": "Summarize the report in a formal and succinct manner. Include the main issue, a brief description of the problem, and its location or context.",\n'
                '  "suggest_priority_id": "Evaluate the severity and urgency of the issue and assign a numerical priority accordingly. Use the following guidelines: \n'
                '    - 1 (LOW): Minor issues that have little or no impact on user safety or functionality (e.g., a small cleaning problem or a minor cosmetic issue). \n'
                '    - 2 (MEDIUM): Issues that may moderately affect user experience or convenience but do not pose an immediate threat (e.g., moderate delays in service or minor maintenance issues). \n'
                '    - 3 (HIGH): Problems that significantly disrupt service or create safety concerns (e.g., major maintenance issues, safety risks on public infrastructure). \n'
                '    - 4 (CRITICAL): Urgent issues that pose an immediate danger, severe disruption, or could result in significant harm (e.g., structural failures, accidents, or conditions that threaten lives)."\n'
                "}\n\n"
                "Report:\n"
                f"{json.dumps(report_data, ensure_ascii=False, indent=2)}"
            )

            model_response = bedrock_worker.run_model(prompt)

            generated_output = model_response

            content_list = generated_output.get("output", {}).get("message", {}).get("content", [])
            if content_list and isinstance(content_list, list):
                json_str = content_list[0].get("text", "").strip()
                parsed_data = json.loads(json_str)
                recommendation = parsed_data.get("recommendation", "")
                short_answer = parsed_data.get("short_answer", "")
                offisial_summary = parsed_data.get("offisial_summary", "")
                suggest_priority_id = parsed_data.get("suggest_priority_id", None)

            if any(x is None or x == "" for x in [recommendation, short_answer, offisial_summary, suggest_priority_id]):
                print(f"Incomplete model response for report_id {report_id}: {generated_output}")
                continue

            db_worker.create_report_details_with_ai_answer(
                report_id, recommendation, short_answer, offisial_summary, suggest_priority_id)

            print(f"Report {report_id} has been successfully processed and recorded into the database.")
        except Exception as e:
            print(f"Error processing report_id {report_id}: {e}")
            
