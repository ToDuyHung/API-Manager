# EXTRACTED FROM USER AND CONVERSATION INFO
DEFAULT_TAG = "default"
USER_PROVIDE_DATA = "User@provide_data"
USER_HAS_MESSAGE = "User@has_message"
USER_MENTION_OBJECT = "User@mention_object"
USER_MENTION_OLD_OBJECT = "User@mention_old_object"
USER_MENTION_UNCLEAR_OBJECTS = "User@mention_unclear_object"
USER_MENTIONED_OBJECT = "User@mentioned_object"
USER_ASK_PRODUCT_INVENTORY = "User@request_product_inventory"

BOT_UPDATE_USER_ATTRIBUTE_STATUS = "Bot@update_user_attribute_status"
BOT_BASE_USER_HAS_ATTRIBUTE = "Bot@user_has_attribute"
BOT_BASE_USER_HAS_MULTI = "Bot@user_has_multi"

BOT_BASE_USER_MISSING_INFO = "Bot@user_missing_info"
BOT_BASE_SHOP_MISSING_INFO = "Bot@shop_missing_info"
BOT_BASE_BILL_MISSING_INFO = "Bot@bill_missing_info"

USER_MULTI_VALUE = "Bot@user_multi_value"
BOT_MULTI_OBJECTS = "Bot@multi_objects"
BOT_PRODUCT_HAS_DISCOUNT = "Bot@product_has_discount"
BOT_ZERO_INVENTORY = "Bot@zero_inventory"
BOT_HAVE_INVENTORY = "Bot@have_inventory"
BOT_OBJECT_NOT_FOUND = "Bot@object_not_found"
BOT_INIT_NEW_BILL = "Bot@init_new_bill"
BOT_BILL_CONFIRMED = "Bot@bill_confirmed"
BOT_BILL_PROCESSING = "Bot@bill_processing"
BOT_BILL_EMPTY = "Bot@bill_empty"
BOT_BILL_VALID_PRODUCTS = "Bot@bill_valid_products"
BOT_NONE_CONFIRMED_BILL = "Bot@none_confirmed_bill"
BOT_SINGLE_CONFIRMED_BILL = "Bot@single_confirmed_bill"
BOT_MULTIPLE_CONFIRMED_BILLS = "Bot@multiple_confirmed_bills"
BOT_NONE_OLD_BILL = "Bot@none_old_bill"
BOT_MULTIPLE_OLD_BILLS = "Bot@multiple_old_bills"

# TO BOT ACTION
BOT_CHECK_PRODUCT_HAS_DISCOUNT = "Bot@check_product_has_discount"

BOT_PROCESS_BILL = "Bot@process_bill"
BOT_ADD_PAYMENT_BANK_ACCOUNT_RECOMMENDATIONS = "Bot@add_payment_bank_accounts_recommendations"
BOT_ADD_BILL_PAYMENT_BANK_ACCOUNT = "Bot@add_bill_payment_bank_account"
BOT_REMOVE_BILL_PAYMENT_METHOD = "Bot@remove_bill_payment_method"
BOT_UPDATE_BILL_ADDRESS = "Bot@update_bill_address"
BOT_UPDATE_BILL_PHONE_NUMBER = "Bot@update_bill_phone_number"
BOT_ADD_BILL_PRODUCT = "Bot@add_bill_product"
BOT_ADD_CARE_PRODUCT = "Bot@add_care_product"
BOT_CANCEL_PRODUCT = "Bot@cancel_product"
BOT_CONFIRM_BILL = "Bot@confirm_bill"
BOT_USER_CANCEL_BILL = "Bot@user_cancel_bill"
BOT_UPDATE_PENDING_PAYMENT = "Bot@update_pending_payment"
BOT_CHECK_BILL_INFOR = "Bot@check_bill_infor"

BOT_ADD_OBJECT_RECOMMENDATIONS = "Bot@add_object_recommendations"
BOT_DROP_MULTIPLE_CHOICES = "Bot@drop_multiple_choices"
BOT_REFRESH_MULTIPLE_CHOICES = "Bot@refresh_multiple_choices"
BOT_PROCESS_MULTIPLE_CHOICES = "Bot@process_multiple_choices"
BOT_ADD_MULTIPLE_OBJECT_CHOICE_RECOMMENDATIONS = "Bot@add_multiple_object_choice_recommendations"
BOT_UPDATE_USER_OBJECT_CHOICE = "Bot@update_user_object_choice"
# add multiple choices for user choose
BOT_ADD_PHONE_NUMBER_CHOICES = "Bot@add_phone_number_choices"
BOT_ADD_ADDRESS_CHOICES = "Bot@add_address_choices"
# PENDING DELETE --- BOT_CHECK_USER_MULTI_VALUE = "Bot@check_user_has_multi_value_infor
# -- replace by BOT_UPDATE_USER_ATTRIBUTE_STATUS"

# billing + check object in bill unique
BOT_ADD_MULTIPLE_VALUE_CHOICE_CANDIDATES = "Bot@add_multiple_value_choice_candidates"
BOT_CHECK_BILL_PRODUCT_UNIQUE = "Bot@check_bill_product_unique"
BOT_BILL_PRODUCT_UNIQUE = "Bot@bill_product_unique"
BOT_BILL_PRODUCT_NOT_UNIQUE = "Bot@bill_product_not_unique"
# billing, check required infor of bill
BILL_BASE_HAS_INFOR = "Bot@bill_has"

BOT_CHECK_USER_SEND_PAYMENT = "Bot@check_user_send_payment"
BOT_USER_SEND_PAYMENT = "Bot@user_send_payment"

BOT_USER_CHOOSE_A_VALUE = "Bot@user_choose_a_value"
BOT_USER_CHOOSE_AN_OBJECT = "Bot@user_choose_an_object"
BOT_USER_UNCLEAR_CHOICE = "Bot@user_unclear_choice"
BOT_USER_WRONG_PHONE = "Bot@user_wrong_phone"
BOT_UPDATE_USER_INFOR = "Bot@update_user_infor"
BOT_USER_UPDATED_ADDRESS = "Bot@user_updated_address"
BOT_USER_UPDATED_PHONE = "Bot@user_updated_phone"

BOT_ANSWER_PRODUCT_QUESTION = "Bot@answer_product_question"
BOT_ANSWER_PRODUCT_QUESTION_WITH_INTENT = "Bot@answer_product_question_with_intent"
BOT_HAS_ANSWER = "Bot@has_answer"
BOT_CANNOT_ANSWER = "Bot@cannot_answer"

BOT_ITEM_IN_SHOP = "Bot@item_in_shop"
BOT_ITEM_OUT_SHOP = "Bot@item_out_shop"

BOT_PRODUCT_IMAGE_SEARCH_MODEL = "Bot@product_image_search_model"
BOT_USER_SEND_IMAGE = "Bot@user_send_image"
BOT_USER_SEND_IMAGE_TEXT = "Bot@user_send_image_text"

BOT_UPDATE_WEATHER_INFOR = "Bot@update_weather_infor"
BOT_USER_HAS_LOCATION = "Bot@user_has_location_weather"
BOT_USER_HAS_NO_LOCATION = "Bot@user_has_no_location_weather"
BOT_USER_HAS_TIME_WEATHER = "Bot@user_has_time_weather"
BOT_USER_HAS_NO_TIME_WEATHER = "Bot@user_has_no_time_weather"

# STATE: CANCEL BILL
BOT_CHECK_BILL_PRODUCT_TO_CANCEL = "Bot@check_bill_product_to_cancel"
BOT_ADD_DROP_PRODUCT_CHOICES = "Bot@add_drop_product_choices"
# use in state that user has one product in bill
USER_BILL_HAVE_ONE = "Bot@user_bill_have_one"
# use in state that user has many products in bill
USER_BILL_HAVE_PRODUCTS = "Bot@user_bill_have_products"

# STATE: ask user infor
# use to check number of infor value of user from last orders
BOT_BASE_USER_MULTI_INFO = "Bot@user_multi_value"
BOT_BASE_USER_HAS_ONE_INFO = "Bot@user_has_one"

# STATE: ask user infor
# use to check number of infor value of user from last orders
BOT_CHECK_SHOP_MULTI_VALUE = "Bot@check_shop_has_multi_value_infor"
BOT_BASE_SHOP_MULTI_INFO = "Bot@shop_multi_value"
BOT_BASE_SHOP_HAS_ONE_INFO = "Bot@shop_has_one"
BOT_UPDATE_SHOP_INFOR_MULTIPLE_CHOICES = "Bot@update_shop_infor_multiple_choices"

# STATE: choose order receiving method
BOT_USER_MENTIONED_TIME = "Bot@user_mentioned_time"
BOT_USER_MENTIONED_MONEY = "Bot@user_mentioned_money"
BOT_UPDATE_BILL_RECEIVE_TIME = "Bot@update_bill_receiving_time"
BOT_REMOVE_BILL_RECEIVE_SHOWROOM = "Bot@remove_bill_receiving_showroom"
BOT_UPDATE_BILL_RECEIVE_SHOWROOM = "Bot@update_bill_receiving_showroom"
BOT_UPDATE_BILL_PAYMENT = "Bot@update_bill_payment"
BOT_REMOVE_BILL_PAYMENT = "Bot@remove_bill_payment"
BOT_ADD_SHOWROOM_CHOICES = "Bot@add_showroom_choices"

BASE_BOT_UPDATE_BILL_RECEIVE_METHOD = "Bot@update_bill_receiving_method"
BASE_BOT_UPDATE_BILL_PAYMENT_METHOD = "Bot@update_bill_payment_method"

# size consultant
BOT_CHECK_USER_SIZE = "Bot@check_user_size"
BOT_PREDICT_USER_SIZE = "Bot@predict_user_size"
BOT_UPDATE_USER_SIZE = "Bot@update_user_size"
BOT_UPDATE_BILL_PRODUCT_SIZE = "Bot@update_bill_product_size"
BOT_CHECK_USER_SIZE_REMAIN = "Bot@check_user_size_remain"
USER_SIZE_OUT_OF_STOCK = "Bot@user_size_out_of_stock"
USER_SIZE_AVAILABLE = "Bot@user_size_available"
BOT_MENTIONED_SIZE_NOT_IN_TABLE = "Bot@mentioned_size_not_in_table"
BOT_CHECK_MENTIONED_SIZE_IN_TABLE = "Bot@check_mentioned_size_in_table"

BOT_CHECK_USER_HISTORY_BILL = "Bot@check_user_history_bill"
BOT_USER_NO_HISTORY_BILL = "Bot@user_no_history_bill"
BOT_USER_HAS_HISTORY_BILL = "Bot@user_has_history_bill"

# NOTE: STATE - Check order status
BOT_GET_CHOSEN_BILL = "Bot@get_chosen_bill"
BOT_CHECK_NUMBER_OF_PROCESSING_BILLS = "Bot@check_number_of_processing_bills"
BOT_ADD_BILLS_TO_CHECK_ORDER_STATUS = "Bot@add_bills_to_check_order_status"
BOT_DROP_BILLS_AFTER_CHECK_ORDER_STATUS = "Bot@drop_bills_after_check_order_status"
BOT_USER_NO_PROCESSING_BILL = "Bot@user_no_processing_bill"

BOT_FORWARD_TO_ADMIN = "Bot@forward_to_admin"
