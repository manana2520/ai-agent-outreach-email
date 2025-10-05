#!/usr/bin/env python
import sys
import os
import json
import argparse

from sales_personalized_email.crew import SalesPersonalizedEmailCrew

# This main file is intended to be a way for your to run your
# crew locally, so refrain from adding necessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information


def run():
    """
    Run the crew with inputs from command line arguments or environment variables.
    Matches the exact parameters and optionality from the Streamlit app.
    """
    parser = argparse.ArgumentParser(description='Run the Sales Personalized Email Crew')
    # Required fields (marked with * in Streamlit)
    parser.add_argument('--first_name', type=str, help='First Name * (required)')
    parser.add_argument('--last_name', type=str, help='Last Name * (required)')  
    parser.add_argument('--company', type=str, help='Company / Account * (required)')
    
    # Optional fields (marked as optional in Streamlit)
    parser.add_argument('--title', type=str, default='', help='Title (optional)')
    parser.add_argument('--phone', type=str, default='', help='Phone (optional)')
    parser.add_argument('--country', type=str, default='', help='Country (optional)')
    parser.add_argument('--linkedin_profile', type=str, default='', help='LinkedIn Profile (optional)')
    parser.add_argument('--selling_intent', type=str, default='', help='Selling Intent / Use Case (optional)')
    
    # JSON input option
    parser.add_argument('--json_input', type=str, help='JSON string with all inputs')
    
    args = parser.parse_args()
    
    # If JSON input is provided, use it
    if args.json_input:
        try:
            inputs = json.loads(args.json_input)
        except json.JSONDecodeError:
            print("Error: Invalid JSON input")
            sys.exit(1)
    # Otherwise, use command line arguments or defaults
    else:
        # Check required fields
        if not args.first_name and not os.getenv('FIRST_NAME'):
            print("Error: first_name is required (use --first_name or set FIRST_NAME env var)")
            sys.exit(1)
        if not args.last_name and not os.getenv('LAST_NAME'):
            print("Error: last_name is required (use --last_name or set LAST_NAME env var)")
            sys.exit(1)
        if not args.company and not os.getenv('COMPANY'):
            print("Error: company is required (use --company or set COMPANY env var)")
            sys.exit(1)
            
        inputs = {
            "first_name": args.first_name or os.getenv('FIRST_NAME'),
            "last_name": args.last_name or os.getenv('LAST_NAME'),
            "title": args.title or os.getenv('TITLE', ''),
            "company": args.company or os.getenv('COMPANY'),
            "phone": args.phone or os.getenv('PHONE', ''),
            "country": args.country or os.getenv('COUNTRY', ''),
            "linkedin_profile": args.linkedin_profile or os.getenv('LINKEDIN_PROFILE', ''),
            "selling_intent": args.selling_intent or os.getenv('SELLING_INTENT', ''),
        }
    
    print(f"Running crew with inputs: {json.dumps(inputs, indent=2)}")
    SalesPersonalizedEmailCrew().crew().kickoff(inputs=inputs)


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {"topic": "AI LLMs"}
    try:
        SalesPersonalizedEmailCrew().crew().train(
            n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        SalesPersonalizedEmailCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {"topic": "AI LLMs"}
    try:
        SalesPersonalizedEmailCrew().crew().test(
            n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")
