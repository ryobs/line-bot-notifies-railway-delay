"""users_table操作用モジュール"""

import os
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from aws.dynamodb import utils
from aws.dynamodb.users import DelayInfoMessages, User
from aws.exceptions import DynamoDBError

users_table = utils.db.Table(os.environ['AWS_USERS_TABLE'])


def put_user(user_id: str) -> dict:
    """ユーザ情報を登録する

    Args:
        user_id: ユーザID

    Raises:
        e: ユーザ情報の登録に失敗

    Returns:
        dict: ユーザ情報の登録結果
    """
    timestamp_now = Decimal(int(datetime.utcnow().timestamp()))
    user = User(user_id, timestamp_now, timestamp_now)
    try:
        response = users_table.put_item(
            Item=utils.replace_data(user.to_dict()))
    except Exception as e:
        raise e
    return response


def update_user(user_id: str, delay_info_messages: DelayInfoMessages) -> dict:
    """ユーザ情報を更新する

    Args:
        user_id: ユーザID
        delay_info_messages: 鉄道遅延情報メッセージ群

    Raises:
        e: ユーザ情報の更新に失敗

    Returns:
        dict: ユーザ情報の更新結果
    """
    key = {'user_id': user_id}
    expression = "set #delay_info_messages=:delay_info_messages, #updated_time=:updated_time"
    expression_name = {
        '#delay_info_messages': 'delay_info_messages',
        '#updated_time': 'updated_time'
    }
    expression_value = {
        ':delay_info_messages': delay_info_messages.to_dict(),
        ':updated_time': int(datetime.utcnow().timestamp()),
    }
    return_value = "UPDATED_NEW"
    try:
        response = users_table.update_item(
            Key=key,
            UpdateExpression=expression,
            ExpressionAttributeNames=expression_name,
            ExpressionAttributeValues=utils.replace_data(expression_value),
            ReturnValues=return_value
        )
    except Exception as e:
        raise e
    return response


def update_railway(delay_info_messages: DelayInfoMessages) -> dict:
    """鉄道用ユーザ情報を更新する

    Args:
        delay_info_messages:  鉄道遅延情報メッセージ群

    Returns:
        dict: 鉄道用ユーザ情報の更新結果
    """
    return update_user("railway", delay_info_messages)


def delete_user(user_id: str) -> dict:
    """ユーザ情報を削除する

    Args:
        user_id: ユーザID

    Raises:
        e: ユーザ情報の削除に失敗

    Returns:
        dict: ユーザ情報の削除結果
    """
    key = {'user_id': user_id}
    try:
        response = users_table.delete_item(Key=key)
    except Exception as e:
        raise e
    return response


def get_user(user_id: str) -> Optional[User]:
    """ユーザ情報を取得する

    Args:
        user_id: ユーザID

    Raises:
        e: ユーザ情報の取得に失敗

    Returns:
        Optional[User]: ユーザ情報
    """
    key = {'user_id': user_id}
    try:
        response = users_table.get_item(Key=key)
    except Exception as e:
        raise e
    item = response.get('Item')
    return User(item['user_id'], item.get('created_time'), item.get(
        'updated_time'), item.get('delay_info_messages')) if item else None


def get_railway() -> User:
    """鉄道用ユーザ情報を取得する

    Raises:
        DynamoDBError: 鉄道用ユーザ情報が登録されていない

    Returns:
        User: 鉄道用ユーザ情報
    """
    railway_user = get_user("railway")
    if railway_user is None:
        raise DynamoDBError("鉄道用ユーザ情報が登録されていません。")
    return railway_user


def scan_exclude_railway() -> List[User]:
    """鉄道用ユーザを除く全ユーザ情報を取得する

    Raises:
        e: ユーザ情報の取得に失敗

    Returns:
        List[User]: 鉄道用ユーザを除く全ユーザ情報リスト
    """
    scan_kwargs = {
        'FilterExpression': 'user_id  <> :user_id',
        'ExpressionAttributeValues': {':user_id': 'railway'}
    }
    try:
        response = users_table.scan(**scan_kwargs)
    except Exception as e:
        raise e
    users = [
        User(
            item['user_id'],
            item.get('created_time'),
            item.get('updated_time'),
            item.get('delay_info_messages')) for item in response['Items']]
    return users
