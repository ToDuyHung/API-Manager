from typing import Dict, Callable

from TMTChatbot.Common.storage.base_storage import BaseStorage
from TMTChatbot.Common.default_intents import *
from TMTChatbot.Common.common_keys import *
from TMTChatbot.AlgoClients.weather_service import WeatherService
from TMTChatbot.Schema.common.billing_method import ShipMethod, PaymentMethod
from TMTChatbot.ServiceWrapper.services.base_service import BaseServiceSingleton
from TMTChatbot.StateController.services.information_extractor import BaseInformationExtractor
from TMTChatbot.StateController.services.shop_manager import ShopManager
from TMTChatbot.StateController.services.user_manager import UserManager
from TMTChatbot.StateController.services.value_mapping import ValueMapping
from TMTChatbot.StateController.services.bot_intent import BotIntent
from TMTChatbot.StateController.services.billing_service import BillingManager
from TMTChatbot.StateController.services.multiple_choice_manager import MultipleChoiceManager
from TMTChatbot.StateController.services.qa_service import QAService
from TMTChatbot.StateController.config.config import Config
from TMTChatbot.StateController.services.product_search_manager import ProductSearchManager
from TMTChatbot.StateController.services.recommendation_manager import RecommendationManager
from TMTChatbot.StateController.services.size_consultant_manager import SizeConsultantManager
from TMTChatbot.Schema.objects.conversation import Conversation


class ActionManager(BaseServiceSingleton):
    def __init__(self, storage: BaseStorage, config: Config):
        super(ActionManager, self).__init__(config=config)
        self.information_extractor = BaseInformationExtractor(config=config, storage=storage)
        self.bot_intent_extractor = BotIntent(config=config, storage=storage)
        self.value_mapper = ValueMapping(config=config, storage=storage)
        self.billing_manager = BillingManager(config=config, storage=storage)
        self.user_manager = UserManager(config=config, storage=storage)
        self.shop_manager = ShopManager(config=config, storage=storage)
        self.multiple_choice_manager = MultipleChoiceManager(config=config, storage=storage)
        self.product_search_manager = ProductSearchManager(config=config, storage=storage)
        self.recommendation_manager = RecommendationManager(config=config, storage=storage)
        self.size_consultant_manager = SizeConsultantManager(config=config, storage=storage)
        self.qa_services = QAService(config=config, storage=storage)
        self.weather_services = WeatherService(config=config, storage=storage)
        self.actions: Dict[str, Callable[[Conversation], ...]] = {
            BOT_CHECK_PRODUCT_HAS_DISCOUNT: self.billing_manager.check_product_discount,

            BOT_ADD_MULTIPLE_VALUE_CHOICE_CANDIDATES: self.multiple_choice_manager.add_multiple_value_choices,
            BOT_PROCESS_MULTIPLE_CHOICES: self.multiple_choice_manager.process_state,
            BOT_DROP_MULTIPLE_CHOICES: self.multiple_choice_manager.drop_multiple_choices,
            BOT_REFRESH_MULTIPLE_CHOICES: self.multiple_choice_manager.refresh_multiple_choices,
            BOT_ADD_OBJECT_RECOMMENDATIONS: self.recommendation_manager.add_product_recommendations,
            BOT_ADD_MULTIPLE_OBJECT_CHOICE_RECOMMENDATIONS: self.recommendation_manager.add_product_multiple_choices,
            BOT_UPDATE_USER_ATTRIBUTE_STATUS: self.user_manager.update_user_attribute_status(False),
            # BOT_CHECK_USER_MULTI_VALUE: self.user_manager.check_user_multi_value(False),
            BOT_CHECK_SHOP_MULTI_VALUE: self.shop_manager.check_shop_multi_value(False),

            BOT_CHECK_BILL_PRODUCT_UNIQUE: self.multiple_choice_manager.unique_bill_object(False),
            BOT_ADD_BILL_PRODUCT: self.billing_manager.add_billing_product,
            BOT_ADD_CARE_PRODUCT: self.billing_manager.add_care_product,
            BOT_ADD_PAYMENT_BANK_ACCOUNT_RECOMMENDATIONS: self.billing_manager.add_payment_bank_account_recommendations,
            BOT_ADD_BILL_PAYMENT_BANK_ACCOUNT: self.billing_manager.add_bill_payment_bank_account,
            BOT_CANCEL_PRODUCT: self.billing_manager.cancel_product,
            BOT_CONFIRM_BILL: self.billing_manager.confirm_bill,
            BOT_PROCESS_BILL: self.billing_manager.process_bill,
            BOT_CHECK_BILL_INFOR: self.billing_manager.check_bill_infor,
            BOT_UPDATE_BILL_ADDRESS: self.billing_manager.update_bill_info(BILL_ADDRESS),
            BOT_UPDATE_BILL_PHONE_NUMBER: self.billing_manager.update_bill_info(BILL_PHONE_NUMBER),
            BOT_UPDATE_PENDING_PAYMENT: self.billing_manager.update_pending_payment,
            BOT_CHECK_USER_SEND_PAYMENT: self.billing_manager.bill_image_service,

            BOT_ANSWER_PRODUCT_QUESTION: self.qa_services.answer_user_product_question,
            BOT_ANSWER_PRODUCT_QUESTION_WITH_INTENT: self.qa_services.answer_user_product_question_with_intent,

            BOT_PRODUCT_IMAGE_SEARCH_MODEL: self.product_search_manager.node_product_image_search,
            BOT_UPDATE_WEATHER_INFOR: self.weather_services.update_weather_infor,

            BOT_CHECK_BILL_PRODUCT_TO_CANCEL: self.billing_manager.check_bill_product_to_cancel,
            BOT_ADD_DROP_PRODUCT_CHOICES: self.multiple_choice_manager.add_drop_product_choices,

            BOT_ADD_PHONE_NUMBER_CHOICES: self.multiple_choice_manager.add_infor_multiple_choices(BILL_PHONE_NUMBER,
                                                                                                  CONV_USER),
            BOT_ADD_ADDRESS_CHOICES: self.multiple_choice_manager.add_infor_multiple_choices(BILL_ADDRESS, CONV_USER),
            BOT_UPDATE_USER_INFOR: self.user_manager.update_user_infor_multiple_choices,
            BOT_UPDATE_SHOP_INFOR_MULTIPLE_CHOICES: self.shop_manager.update_shop_infor_multiple_choices,

            BOT_REMOVE_BILL_RECEIVE_SHOWROOM: self.billing_manager.remove_bill_attribute(BILL_RECEIVE_SHOWROOM),
            BOT_REMOVE_BILL_PAYMENT_METHOD: self.billing_manager.remove_bill_attribute(BILL_PAYMENT_METHOD),
            BOT_UPDATE_BILL_RECEIVE_TIME: self.billing_manager.update_bill_info(BILL_RECEIVE_TIME),
            BOT_UPDATE_BILL_RECEIVE_SHOWROOM: self.billing_manager.update_bill_info(BILL_RECEIVE_SHOWROOM),
            BOT_ADD_SHOWROOM_CHOICES: self.multiple_choice_manager.add_infor_multiple_choices(SHOWROOM, CONV_SHOP),
            BOT_CHECK_USER_SIZE: self.size_consultant_manager.check_user_size(False),
            BOT_PREDICT_USER_SIZE: self.size_consultant_manager.predict_size,
            BOT_UPDATE_USER_SIZE: self.size_consultant_manager.update_user_size,
            BOT_UPDATE_BILL_PRODUCT_SIZE: self.billing_manager.update_bill_product_attr(PRODUCT_SIZE),
            BOT_CHECK_USER_SIZE_REMAIN: self.size_consultant_manager.check_user_size_remain,
            BOT_CHECK_MENTIONED_SIZE_IN_TABLE: self.size_consultant_manager.check_mentioned_size_in_table,

            BOT_UPDATE_BILL_PAYMENT: self.billing_manager.update_bill_info(BILL_PAYMENT),
            BOT_REMOVE_BILL_PAYMENT: self.billing_manager.remove_bill_attribute(BILL_PAYMENT),

            # NOTE: State - Check Order Status
            BOT_GET_CHOSEN_BILL: self.billing_manager.get_chosen_bill,
            BOT_ADD_BILLS_TO_CHECK_ORDER_STATUS: self.billing_manager.add_bills_to_check_order_status,
            BOT_CHECK_NUMBER_OF_PROCESSING_BILLS: self.billing_manager.check_number_of_processing_bills,
            BOT_DROP_BILLS_AFTER_CHECK_ORDER_STATUS: self.billing_manager.drop_bills_after_check_order_status,

            BOT_CHECK_USER_HISTORY_BILL: self.user_manager.check_user_history_bill,
            BOT_FORWARD_TO_ADMIN: self.shop_manager.forward_to_admin
        }
        self.add_update_bill_receive_method()
        self.add_update_bill_payment_method()

    def add_update_bill_receive_method(self):
        [self.add_action(action_name=f"{BASE_BOT_UPDATE_BILL_RECEIVE_METHOD}_{ship_method}",
                         action_function=self.billing_manager.update_bill_infor_with_value(BILL_RECEIVE_METHOD,
                                                                                           ship_method))
         for ship_method in ShipMethod.keys()]

    def add_update_bill_payment_method(self):
        [self.add_action(action_name=f"{BASE_BOT_UPDATE_BILL_PAYMENT_METHOD}_{payment_method}",
                         action_function=self.billing_manager.update_bill_infor_with_value(BILL_PAYMENT_METHOD,
                                                                                           payment_method))
         for payment_method in PaymentMethod.keys()]

    def add_action(self, action_name, action_function):
        if action_name in self.actions:
            raise ValueError(f"{action_name} already exist. Please use different action_name")
        self.actions[action_name] = action_function

    def map_bot_expectation(self, conversation: Conversation):
        self.information_extractor.map_bot_expectation(conversation)

    def default_global_actions(self, conversation: Conversation):
        pass

    def default_pre_actions(self, conversation: Conversation, is_new_action: bool = False,
                            mapping_info_only: bool = False):
        """
        Some task must be done in every conversation turn to extract basic information from users
        :param conversation:
        :param is_new_action:
        :param mapping_info_only:
        :return:
        """
        if mapping_info_only:
            self.information_extractor.mapping_info(conversation)
        else:
            self.information_extractor.information_extraction(conversation, is_new_action)
            self.information_extractor.mapping_info(conversation, is_new_action)
            self.bot_intent_extractor.extract_state_based_intents(conversation)

    def make_pre_actions(self, conversation: Conversation, is_new_action: bool = False,
                         mapping_info_only: bool = False):
        """
        Looking for action in PRE ACTIONS to execute the appropriate function
        :param conversation:
        :param is_new_action:
        :param mapping_info_only:
        :return:
        """
        self.default_pre_actions(conversation=conversation, is_new_action=is_new_action,
                                 mapping_info_only=mapping_info_only)
        current_action = conversation.current_action
        if current_action is not None:
            for pre_action in current_action.pre_actions.values():
                if pre_action.tag in self.actions:
                    func = self.actions[pre_action.tag]
                    func(conversation)
                else:
                    self.logger.warning(f"Func {pre_action.tag} not Implemented")

    def make_post_actions(self, conversation: Conversation):
        """
        Looking for action in POST ACTIONS to execute the appropriate function
        :param conversation:
        :return:
        """
        current_action = conversation.current_action
        if current_action is not None:
            for post_action in current_action.post_actions.values():
                if post_action.tag in self.actions:
                    func = self.actions[post_action.tag]
                    func(conversation)
                else:
                    self.logger.warning(f"Func {post_action.tag} not Implemented")

    def make_current_action(self, conversation: Conversation):
        """
        Looking for action in CURRENT DONE BRANCH to execute the appropriate function
        :param conversation:
        :return:
        """
        current_action = conversation.current_action
        if current_action is not None:
            current_branch = current_action.current_branch
            if current_branch is not None:
                self.logger.debug(f"POST ACTIONS {current_action.name, current_branch.post_actions.values()}")
                for current_action in current_branch.post_actions.values():
                    if current_action.tag in self.actions:
                        func = self.actions[current_action.tag]
                        func(conversation)
                    else:
                        self.logger.warning(f"Func {current_action.tag} not Implemented")
