import aiohttp
import asyncio
import csv
import re
from playwright.async_api import async_playwright
from termcolor import colored
from datetime import datetime


def get_twitter_accounts():
    with open("twitter.csv", "r", newline="") as f:
        reader = csv.DictReader(f)
        return [row['TWITTER USERNAME'] for row in reader]


async def get_twitter_cookies(playwright):
    browser = await playwright.chromium.launch()
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto("https://twitter.com/trxsh_cook")
    cookies = [{"name": cookie["name"], "value": cookie["value"]} for cookie in await context.cookies("https://twitter.com/trxsh_cook")]
    return cookies


async def get_twitter_token(session):
    response = await session.get("https://abs.twimg.com/responsive-web/client-web/main.63264d76.js")
    text = await response.text()
    token = "Bearer " + re.findall(r's="(A.{103})"', text)[0]
    return token


def make_tasks(session, accounts, cookies, user_token):
    tasks = list()
    for account in accounts:

        querystring = {
            "variables": "{\"screen_name\":\"" + account + "\",\"withSafetyModeUserFields\":true,\"withSuperFollowsUserFields\":true}"
        }

        headers = {
            'cookie': cookies[0]["value"],
            'authorization': user_token,
            'x-guest-token': cookies[2]["value"]
        }

        t = session.get("https://twitter.com/i/api/graphql/Bhlf1dYJ3bYCKmLfeEQ31A/UserByScreenName", headers=headers, params=querystring)
        tasks.append(t)

    return tasks


def parse_results(json_responses):
    accounts = list()
    for json_response in json_responses:
        account_status = json_response["data"]["user"]["result"]["legacy"]["profile_interstitial_type"]
        account_name = json_response["data"]["user"]["result"]["legacy"]["screen_name"]
        if account_status == "fake_account":
            accounts.append({"username": account_name, "limited": "Yes", "reasoning": account_status})
            print(colored(f"{datetime.now()} | {account_name} is b4nned...", "red"))
        else:
            accounts.append({"username": account_name, "limited": "No", "reasoning": ""})
            print(colored(f"{datetime.now()} | {account_name} is f1ne :)...", "green"))

    return accounts


def log_results(accounts):
    with open("results.csv", "w", newline="") as f:
        headers = ["TWITTER USERNAME", "BANNED?",  "REASONING"]
        writer = csv.DictWriter(f, headers)
        writer.writeheader()
        [writer.writerow({"TWITTER USERNAME": account["username"], "BANNED?": account["limited"], "REASONING": account["reasoning"]}) for account in accounts]


async def main():

    account_results = list()

    accounts = get_twitter_accounts()
    print(colored(f"{datetime.now()} | Getting tw1tter cookies...", "yellow"))

    async with async_playwright() as p:
        cookies = await get_twitter_cookies(p)
        print(colored(f"{datetime.now()} | Got tw1tter cookies...", "yellow"))

    print(colored(f"{datetime.now()} | Starting to check {len(accounts)} tw1tter accounts...", "yellow"))

    async with aiohttp.ClientSession() as s:
        token = await get_twitter_token(s)
        tasks = make_tasks(s, accounts, cookies, token)
        results = await asyncio.gather(*tasks)
        for result in results:
            json_result = await result.json()
            account_results.append(json_result)

    end_results = parse_results(account_results)
    log_results(end_results)
    print(colored(f"{datetime.now()} | L0gged all results to results.csv", "yellow"))
    print(colored(f"{datetime.now()} | W3're done, feel free to close :)", "yellow"))
    print(colored(f"{datetime.now()} | M4de by pepegan't#0409 with 🥰", "yellow"))
    input()


asyncio.run(main())