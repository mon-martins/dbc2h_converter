# DBC to Header File Converter

This python reads a dbc file using the cantools library then generates generic header C file with the CAN_SIG_ENCODE, CAN_SIG_DECODE and CAN_SIG_IS_VALID macros.

## Example:

- message name: MY_MESSAGE
- signal name: MY_SIGNAL

usage:

### Receiving:

a data arrives in CAN:

// generic funcion to read a message and returns the payload
uint64_t message_payload = read_message();

then

my_sig_type_t my_sig;
my_sig = CAN_SIG_DECODE(CAN_MSG_MY_MESSAGE, CAN_SIG_MY_SIGNAL, message_payload);

if( !CAN_SIG_IS_VALID(CAN_MSG_MY_MESSAGE, CAN_SIG_MY_SIGNAL, my_sig)) some_error();
else proceed();

### Sending:

a signal to send:

my_sig_type_t my_sig = A_VALUE;

// declare a struct to send the message
CAN_MSG_MY_MESSAGE_t payload_to_send;

if( !CAN_SIG_IS_VALID(CAN_MSG_MY_MESSAGE, CAN_SIG_MY_SIGNAL, my_sig)) some_error();

payload_to_send.CAN_SIG_MY_SIGNAL = CAN_SIG_ENCODE(CAN_MSG_MY_MESSAGE, CAN_SIG_MY_SIGNAL, my_sig);

// generic funcion to send a message with the payload passed
send_message(payload);
