import boto3
import pytest
from botocore.exceptions import ClientError
import json
import time
from moto import mock_iam
from unittest.mock import patch

POLICY_NAME = 'TestIAMPolicy'
TEST_USER_NAME = 'TestIAMUser'

POLICY_DOCUMENT = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "iam:ListUsers",
                "iam:GetUser",
                "iam:ListGroups",
                "iam:GetGroup"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Deny",
            "Action": [
                "iam:CreateUser",
                "iam:DeleteUser",
                "iam:UpdateUser",
                "iam:CreateGroup",
                "iam:DeleteGroup"
            ],
            "Resource": "*"
        }
    ]
}

@pytest.fixture(scope="module")
def iam_setup():
    with mock_iam():
        iam_client = boto3.client('iam', region_name='us-east-1')
        
        # Creation of Policy
        try:
            response = iam_client.create_policy(
                PolicyName=POLICY_NAME,
                PolicyDocument=json.dumps(POLICY_DOCUMENT)
            )
            policy_arn = response['Policy']['Arn']
            print(f"Policy {POLICY_NAME} created with ARN {policy_arn}.")
            time.sleep(1)
        except ClientError as e:
            pytest.fail(f"Failed to create policy: {e}")
        
        # Creation of test user
        try:
            iam_client.create_user(UserName=TEST_USER_NAME)
            print(f"User {TEST_USER_NAME} created.")
            iam_client.attach_user_policy(
                UserName=TEST_USER_NAME,
                PolicyArn=policy_arn
            )
            print(f"Policy {POLICY_NAME} attached to user {TEST_USER_NAME}.")
            time.sleep(1)
        except ClientError as e:
            pytest.fail(f"Failed to create or attach policy to user: {e}")
        
        yield iam_client, policy_arn
        
        # Cleanup: policy and user
        try:
            iam_client.detach_user_policy(
                UserName=TEST_USER_NAME,
                PolicyArn=policy_arn
            )
            print(f"Policy {POLICY_NAME} detached from user {TEST_USER_NAME}.")
            iam_client.delete_user(UserName=TEST_USER_NAME)
            print(f"User {TEST_USER_NAME} deleted.")
            iam_client.delete_policy(PolicyArn=policy_arn)
            print(f"Policy {POLICY_NAME} deleted.")
        except ClientError as e:
            print(f"Error during cleanup: {e}")

def test_allowed_actions(iam_setup):
    """
    Test allowed actions
    """
    iam_client, policy_arn = iam_setup
    try:
        # List Users
        response = iam_client.list_users()
        assert 'Users' in response
        print("ListUsers action allowed.")
        
        # Get User
        response = iam_client.get_user(UserName=TEST_USER_NAME)
        assert response['User']['UserName'] == TEST_USER_NAME
        print("GetUser action allowed.")
        
        # List Groups
        response = iam_client.list_groups()
        assert 'Groups' in response
        print("ListGroups action allowed.")
        
        # Get Group
        # Creation of group for testing
        group_name = 'TestGroup'
        iam_client.create_group(GroupName=group_name)
        response = iam_client.get_group(GroupName=group_name)
        assert 'Group' in response
        print(f"GetGroup action allowed for group {group_name}.")
    except ClientError as e:
        pytest.fail(f"Allowed action failed: {e}")

def raise_access_denied(*args, **kwargs):
    """
    Function for imitation of AccessDenied error.
    """
    raise ClientError(
        error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
        operation_name='Operation'
    )

def test_denied_actions(iam_setup):
    """
    Test denied actions, to make sure, that they provide AccessDenied error.
    """
    iam_client, policy_arn = iam_setup
    # Действия, которые должны быть запрещены
    denied_actions = [
        ('create_user', {'UserName': 'DeniedUser'}),
        ('delete_user', {'UserName': 'DeniedUser'}),
        ('update_user', {'UserName': 'DeniedUser', 'NewPath': '/'}),
        ('create_group', {'GroupName': 'DeniedGroup'}),
        ('delete_group', {'GroupName': 'DeniedGroup'})
    ]
    
    for action, params in denied_actions:
        with patch.object(iam_client, action, side_effect=raise_access_denied):
            with pytest.raises(ClientError) as excinfo:
                getattr(iam_client, action)(**params)
            error_code = excinfo.value.response['Error']['Code']
            assert error_code == 'AccessDenied', f"Expected AccessDenied, got {error_code}"
            print(f"{action} action correctly denied.")
