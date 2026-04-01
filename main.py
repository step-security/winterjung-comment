import json
import os
import sys
from http import HTTPStatus
from typing import Optional, Tuple

import requests

GITHUB_API_BASE_URL = os.environ.get('GITHUB_API_URL', 'https://api.github.com')
STEPSECURITY_API_BASE_URL = 'https://agent.api.stepsecurity.io'


def escape(v: str) -> str:
    return repr(v)[1:-1]


def set_action_output(name: str, value: str):
    github_output = os.environ.get('GITHUB_OUTPUT', '')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f'{name}={value}\n')
    else:
        sys.stdout.write(f'::set-output name={name}::{escape(value)}\n')


def print_action_error(msg: str):
    sys.stdout.write(f'::error file={__name__}::{escape(msg)}\n')


def print_action_debug(msg: str):
    sys.stdout.write(f'::debug file={__name__}::{escape(msg)}\n')


def get_action_input(
    name: str, required: bool = False, default: Optional[str] = None
) -> str:
    v = os.environ.get(f'INPUT_{name.upper()}', '')
    if v == '' and default:
        v = default
    if required and v == '':
        print_action_error(f'input required and not supplied: {name}')
        exit(1)
    return v


def create(token, repo, body, issue_number) -> Tuple[str, str]:
    headers = {
        'Authorization': f'token {token}',
    }
    data = {
        'body': body,
    }
    resp = requests.post(
        f'{GITHUB_API_BASE_URL}/repos/{repo}/issues/{issue_number}/comments',
        headers=headers,
        json=data,
    )
    if resp.status_code != HTTPStatus.CREATED:
        print_action_error(f'cannot create comment')
        print_action_debug(f'status code: {resp.status_code}')
        print_action_debug(f'response body: {resp.text}')
        exit(1)

    json = resp.json()
    return str(json['id']), body


def edit(token, repo, body, comment_id) -> Tuple[str, str]:
    headers = {
        'Authorization': f'token {token}',
    }
    data = {
        'body': body,
    }
    resp = requests.patch(
        f'{GITHUB_API_BASE_URL}/repos/{repo}/issues/comments/{comment_id}',
        headers=headers,
        json=data,
    )
    if resp.status_code != HTTPStatus.OK:
        print_action_error(f'cannot edit comment')
        print_action_debug(f'status code: {resp.status_code}')
        print_action_debug(f'response body: {resp.text}')
        exit(1)

    json = resp.json()
    return str(json['id']), body


def delete(token, repo, comment_id) -> Tuple[str, str]:
    headers = {
        'Authorization': f'token {token}',
    }
    resp = requests.delete(
        f'{GITHUB_API_BASE_URL}/repos/{repo}/issues/comments/{comment_id}',
        headers=headers,
    )
    if resp.status_code != HTTPStatus.NO_CONTENT:
        print_action_error(f'cannot delete comment')
        print_action_debug(f'status code: {resp.status_code}')
        print_action_debug(f'response body: {resp.text}')
        exit(1)

    return '', ''


def check_subscription():
    upstream = 'winterjung/comment'
    docs_url = 'https://docs.stepsecurity.io/actions/stepsecurity-maintained-actions'
    action = os.environ.get('GITHUB_ACTION_REPOSITORY', '')
    repo = os.environ.get('GITHUB_REPOSITORY', '')

    repo_private = None
    event_path = os.environ.get('GITHUB_EVENT_PATH', '')
    if event_path:
        try:
            with open(event_path) as f:
                payload = json.load(f)
                repo_private = payload.get('repository', {}).get('private')
        except Exception:
            pass

    print()
    print('\033[1;36mStepSecurity Maintained Action\033[0m')
    print(f'Secure drop-in replacement for {upstream}')
    if repo_private is False:
        print('\033[32m\u2713 Free for public repositories\033[0m')
    print(f'\033[36mLearn more:\033[0m {docs_url}')
    print()

    if repo_private is False:
        return

    server_url = os.environ.get('GITHUB_SERVER_URL', 'https://github.com')
    body = {'action': action}
    if server_url != 'https://github.com':
        body['ghes_server'] = server_url

    try:
        resp = requests.post(
            f'{STEPSECURITY_API_BASE_URL}/v1/github/{repo}/actions/maintained-actions-subscription',
            json=body,
            timeout=3,
        )
        if resp.status_code == 403:
            print('\033[1;31mThis action requires a StepSecurity subscription for private repositories.\033[0m', file=sys.stderr)
            print(f'\033[31mLearn how to enable a subscription: {docs_url}\033[0m', file=sys.stderr)
            exit(1)
    except Exception:
        print('Timeout or API not reachable. Continuing to next step.')


def main():
    check_subscription()

    repo = os.environ['GITHUB_REPOSITORY']
    action_type = get_action_input('type', required=True)
    token = get_action_input('token', required=True)
    body = get_action_input('body')
    comment_id = get_action_input('comment_id')
    issue_number = get_action_input('issue_number')

    _id, _body = '', ''
    if action_type == 'create':
        _id, _body = create(token, repo, body, issue_number)
    elif action_type == 'edit':
        _id, _body = edit(token, repo, body, comment_id)
    elif action_type == 'delete':
        _id, _body = delete(token, repo, comment_id)

    set_action_output('id', _id)
    set_action_output('body', _body)


if __name__ == '__main__':
    main()
