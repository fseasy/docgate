"""Credits to copilot"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from docgate.exceptions import InvalidUserInputException
from docgate.logics import CreateDbUserLogic, CreateUserStatus, PrepaidCodeLogic
from docgate.models import PrepaidCode as PrepaidCodeModel, PayLogUnit, Tier, User


@pytest.mark.asyncio
class TestPrepaidCodeLogicBindingDbUser:
  """Test suite for PrepaidCodeLogic.binding_db_user() method"""

  @pytest.fixture
  def db_session(self):
    """Mock async database session"""
    return AsyncMock(spec=AsyncSession)

  @pytest.fixture
  def user_id(self):
    return "test-user-123"

  @pytest.fixture
  def code(self):
    return "abc1234567"

  @pytest.fixture
  def mock_db_user(self):
    """Mock User object with required methods"""
    user = MagicMock(spec=User)
    user.id = "test-user-123"
    user.tier = Tier.FREE
    user.tier_lifetime = None
    user.add_paylog = MagicMock()
    user.last_active_at = datetime.now(tz=timezone.utc)
    return user

  # Test Case 1: code data 不存在
  async def test_binding_db_user_code_not_found(self, db_session, mock_db_user, code):
    """Should raise InvalidUserInputException when code doesn't exist"""
    # Arrange
    with patch("docgate.logics.async_get_prepaid_code", new_callable=AsyncMock) as mock_get_code:
      mock_get_code.return_value = None

      # Act & Assert
      with pytest.raises(InvalidUserInputException):
        await PrepaidCodeLogic.binding_db_user(db_session, mock_db_user, code)

      # Verify user's paylog was added with failure reason
      mock_db_user.add_paylog.assert_called_once()
      call_args = mock_db_user.add_paylog.call_args
      assert "预付款码不存在" in call_args[0][0]
      assert call_args[1]["is_success"] is False

  # Test Case 2: code data 存在但不可 redeem (已使用)
  async def test_binding_db_user_code_not_redeemable_used(self, db_session, mock_db_user, code):
    """Should raise InvalidUserInputException when code is already used"""
    # Arrange
    mock_code_data = MagicMock(spec=PrepaidCodeModel)
    mock_code_data.redeemable_with_reason = (False, "has already been used")

    with patch("docgate.logics.async_get_prepaid_code", new_callable=AsyncMock) as mock_get_code:
      mock_get_code.return_value = mock_code_data

      # Act & Assert
      with pytest.raises(InvalidUserInputException):
        await PrepaidCodeLogic.binding_db_user(db_session, mock_db_user, code)

      # Verify user's paylog was added with failure reason
      mock_db_user.add_paylog.assert_called_once()
      call_args = mock_db_user.add_paylog.call_args
      assert "预付款码已失效" in call_args[0][0]
      assert call_args[1]["is_success"] is False

  # Test Case 3: code data 存在但不可 redeem (已过期)
  async def test_binding_db_user_code_not_redeemable_expired(self, db_session, mock_db_user, code):
    """Should raise InvalidUserInputException when code is expired"""
    # Arrange
    mock_code_data = MagicMock(spec=PrepaidCodeModel)
    mock_code_data.redeemable_with_reason = (False, "has expired")

    with patch("docgate.logics.async_get_prepaid_code", new_callable=AsyncMock) as mock_get_code:
      mock_get_code.return_value = mock_code_data

      # Act & Assert
      with pytest.raises(InvalidUserInputException):
        await PrepaidCodeLogic.binding_db_user(db_session, mock_db_user, code)

  # Test Case 4: code 存在且可 redeem，成功绑定
  async def test_binding_db_user_success(self, db_session, mock_db_user, code):
    """Should successfully bind code to user"""
    # Arrange
    mock_code_data = MagicMock(spec=PrepaidCodeModel)
    mock_code_data.redeemable_with_reason = (True, None)
    mock_code_data.do_binding = MagicMock()

    with patch("docgate.logics.async_get_prepaid_code", new_callable=AsyncMock) as mock_get_code:
      mock_get_code.return_value = mock_code_data

      # Act
      await PrepaidCodeLogic.binding_db_user(db_session, mock_db_user, code)

      # Assert
      # Verify code binding was called
      mock_code_data.do_binding.assert_called_once_with(mock_db_user.id)

      # Verify user tier was upgraded
      assert mock_db_user.tier == Tier.GOLD
      assert mock_db_user.tier_lifetime is None

      # Verify paylog was added with success
      assert mock_db_user.add_paylog.call_count == 1
      call_args = mock_db_user.add_paylog.call_args
      assert "验证预付款码成功" in call_args[0][0]
      assert call_args[1]["is_success"] is True

      # Verify code was added to session
      db_session.add.assert_called_once_with(mock_code_data)


@pytest.mark.asyncio
class TestCreateDbUserLogicAsyncCreateWithRedeeming:
  """Test suite for CreateDbUserLogic.async_create_with_redeeming() method"""

  @pytest.fixture
  def db_session(self):
    """Mock async database session"""
    return AsyncMock(spec=AsyncSession)

  @pytest.fixture
  def user_id(self):
    return "test-user-456"

  @pytest.fixture
  def user_email(self):
    return "test@example.com"

  @pytest.fixture
  def code(self):
    return "code1234567"

  # Test Case 1: code 不存在 - 创建 free user，raise exception
  async def test_async_create_with_redeeming_code_not_found(self, db_session, user_id, user_email, code):
    """Should create free user and raise exception when code doesn't exist"""
    # Arrange
    mock_free_user = MagicMock(spec=User)
    mock_free_user.id = user_id

    with (
      patch("docgate.logics.async_get_prepaid_code", new_callable=AsyncMock) as mock_get_code,
      patch("docgate.logics.async_create_free_user", new_callable=AsyncMock) as mock_create_free,
    ):
      mock_get_code.return_value = None
      mock_create_free.return_value = mock_free_user

      # Act & Assert
      with pytest.raises(InvalidUserInputException):
        await CreateDbUserLogic.async_create_with_redeeming(db_session, user_id, user_email, code)

      # Verify free user was created with correct paylog
      mock_create_free.assert_called_once()
      call_args = mock_create_free.call_args
      assert call_args[1]["user_id"] == user_id
      assert call_args[1]["email"] == user_email
      pay_log_unit = call_args[1]["pay_log_unit"]
      assert isinstance(pay_log_unit, PayLogUnit)
      assert pay_log_unit.is_success is False
      assert "预付款码不存在" in pay_log_unit.log

  # Test Case 2: code 存在但不可 redeem - 创建 free user，raise exception
  async def test_async_create_with_redeeming_code_not_redeemable(self, db_session, user_id, user_email, code):
    """Should create free user and raise exception when code is not redeemable"""
    # Arrange
    mock_code_data = MagicMock(spec=PrepaidCodeModel)
    mock_code_data.redeemable_with_reason = (False, "expired")

    mock_free_user = MagicMock(spec=User)
    mock_free_user.id = user_id

    with (
      patch("docgate.logics.async_get_prepaid_code", new_callable=AsyncMock) as mock_get_code,
      patch("docgate.logics.async_create_free_user", new_callable=AsyncMock) as mock_create_free,
    ):
      mock_get_code.return_value = mock_code_data
      mock_create_free.return_value = mock_free_user

      # Act & Assert
      with pytest.raises(InvalidUserInputException):
        await CreateDbUserLogic.async_create_with_redeeming(db_session, user_id, user_email, code)

      # Verify free user was created with correct paylog
      mock_create_free.assert_called_once()
      call_args = mock_create_free.call_args
      pay_log_unit = call_args[1]["pay_log_unit"]
      assert pay_log_unit.is_success is False
      assert "预付款码失效" in pay_log_unit.log

  # Test Case 3: code 存在且可 redeem - 创建 paid user，返回 success
  async def test_async_create_with_redeeming_success(self, db_session, user_id, user_email, code):
    """Should create paid user and return success when code is valid"""
    # Arrange
    mock_code_data = MagicMock(spec=PrepaidCodeModel)
    mock_code_data.redeemable_with_reason = (True, None)

    mock_paid_user = MagicMock(spec=User)
    mock_paid_user.id = user_id
    mock_paid_user.tier = Tier.GOLD

    with (
      patch("docgate.logics.async_get_prepaid_code", new_callable=AsyncMock) as mock_get_code,
      patch("docgate.logics.async_create_user_with_redeeming_prepaid_code", new_callable=AsyncMock) as mock_create_paid,
    ):
      mock_get_code.return_value = mock_code_data
      mock_create_paid.return_value = mock_paid_user

      # Act
      result = await CreateDbUserLogic.async_create_with_redeeming(db_session, user_id, user_email, code)

      # Assert
      assert result == CreateUserStatus.CREATE_AND_REDEEM_SUCCESS

      # Verify paid user was created with correct parameters
      mock_create_paid.assert_called_once_with(
        db_session, user_id=user_id, email=user_email, prepaid_code=mock_code_data
      )
