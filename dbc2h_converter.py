import cantools
from datetime import datetime

import sys
import os

if(len(sys.argv) < 3): raise Exception("missing parameter, usage: directory_of_dbc name_of_dbc_file system_name")

# dbc path
source_path = sys.argv[1]
# name of your node
system_name = sys.argv[2]

dbc_files = []
dbc_files += [each for each in os.listdir(source_path) if each.endswith('.dbc')]

for file in dbc_files:

    file = str(file)
    source_file = file.removesuffix('.dbc')

    output_file_name = source_file

    dbc_inst = cantools.db.load_file(source_path+"/"+source_file+".dbc")

    header = open(output_file_name + ".h", "w", encoding="utf-8")

    header.write( "/************************************************************/\n")
    header.write( "// Automatically generated C header file from CAN DBC file\n")
    header.write(f"// Source file name: {source_file}.dbc\n")
    header.write(f"// Date created: {datetime.now().strftime('%Y-%m-%d')}\n")
    header.write( "/************************************************************/\n")
    header.write( "\n")
    header.write( "\n")

    header.write( "\n")
    header.write( "\n")
    header.write( "/************************************************************/\n")
    header.write( "//====================Messages Proprieties====================\n")
    header.write( "/************************************************************/\n")
    header.write( "\n")

    mask_ones = 0x00000000
    mask_zeros= 0x00000000

    for message in dbc_inst.messages:
        if system_name in message.receivers:
            mask_ones  |= message.frame_id
            mask_zeros |= ~message.frame_id

    mask_ones  &= 0x00FFFF00
    mask_zeros &= 0x00FFFF00

    receive_id   = f"0x{mask_ones & 0x1FFFFFFF:08x}"
    receive_mask = f"0x{(~(mask_ones^mask_zeros)&0x1FFFFFFF):08x}"

    header.write( "\n")
    header.write( "\n")
    header.write( f"#define CAN_MSG_RECEIVE_ID {receive_id}\n")
    header.write( f"#define CAN_MSG_RECEIVE_MASK {receive_mask}\n")
    header.write( "\n")
    header.write( "\n")

    for message in dbc_inst.messages:
        header.write( "\n")
        header.write( "/************************************************************/\n")
        header.write(f"// Message: {message.name}\n")
        header.write( "/************************************************************/\n")
        header.write(f"#define CAN_MSG_{message.name} CAN_MSG_{message.name}\n")
        header.write(f"#define CAN_MSG_{message.name}_FRAME_ID {hex(message.frame_id)}\n")
        header.write( "\n")
        header.write( "typedef struct{\n")
        
        bit_start = 0
        for signal in message.signals:
            assert bit_start <= signal.start , "Overlaid signals"
            padding_bits = signal.start - bit_start
            if padding_bits>0:
                header.write(f"    // padding {bit_start}-{bit_start+padding_bits-1}\n")
                header.write(f"    uint64_t padding_{bit_start}:{padding_bits};\n")
            bit_start = bit_start+padding_bits

            if signal.is_float:
                if signal.length == 32:
                    sig_type = 'float32_t'
                    if not(bit_start == 0 or bit_start == 32):
                        raise Exception("the float32 value must be init on bit 0 or bit 32")
                elif signal.length ==64:
                    sig_type = 'float64_t'
                    if not(bit_start == 0):
                        raise Exception("the float64 value must be init on bit 0")
                else:
                    raise Exception("A float pointer must be 32bit or 64bit sized")
            elif signal.is_signed:
                sig_type = 'int64_t'
            else:
                sig_type = 'uint64_t'
            
            header.write(f"    // CAN_SIG_{signal.name} , bits {bit_start}-{bit_start+signal.length-1}\n")
            header.write(f"    {sig_type} CAN_SIG_{signal.name}")
            if(not signal.is_float):
                header.write(f":{signal.length}")
            header.write( ";\n")
            bit_start = bit_start + signal.length
        if bit_start<64:
            header.write(f"    // undef {bit_start}-{63} \n")
            header.write(f"    uint64_t undef:{64-bit_start};\n")
        header.write( "}")
        header.write(f"CAN_MSG_{message.name}_t;\n")

        header.write("\n")
        for signal in message.signals:
            header.write(f"// Signal: {signal.name}\n")
            header.write(f"#define CAN_SIG_{signal.name} CAN_SIG_{signal.name}\n")
            if signal.is_signed:
                header.write(f"#define CAN_MSG_{message.name}_CAN_SIG_{signal.name}_TRANSMISSION_TYPE int64_t\n")
            else:
                header.write(f"#define CAN_MSG_{message.name}_CAN_SIG_{signal.name}_TRANSMISSION_TYPE int64_t\n")
            
            if signal.scale != None:
                header.write(f"#define CAN_MSG_{message.name}_CAN_SIG_{signal.name}_SCALE {signal.scale}\n")
            else:
                header.write( "#error \"the scale must be a number\"\n")
                raise Exception(f"the scale of {signal.name} in {message.name} must be a number")
            
            if signal.offset != None:
                header.write(f"#define CAN_MSG_{message.name}_CAN_SIG_{signal.name}_OFFSET {signal.offset}\n")
            else:
                header.write( "#error \"the offset must be a number\"\n")
                raise Exception(f"the offset of {signal.name} in {message.name} must be a number")
            
            if signal.minimum != None:
                header.write(f"#define CAN_MSG_{message.name}_CAN_SIG_{signal.name}_MINIMUM {signal.minimum}\n")
            else:
                header.write( "#error \"the minimum must be a number\"\n")
                raise Exception(f"the minimum of {signal.name} in {message.name} must be a number")
            
            if signal.maximum != None and signal.maximum>signal.minimum:
                header.write(f"#define CAN_MSG_{message.name}_CAN_SIG_{signal.name}_MAXIMUM {signal.maximum}\n")
            else:
                header.write( "#error \"the maximum must be a number\"\n")
                raise Exception(f"the maximum of {signal.name} in {message.name} must be a number and larger than minimum")

            total_size = ( (2**(signal.length)-1) )
            max_encoded = (signal.maximum - signal.offset)/signal.scale
            min_encoded = (signal.minimum - signal.offset)/signal.scale
            
            if signal.is_float:
                pass
            elif signal.is_signed:
                negative_size = -(2**(signal.length-1)-1)
                if( max_encoded > total_size + negative_size):
                    header.write( "#error \"the maximum must fits the space alocated\"\n")
                    raise Exception(f"the maximum of {signal.name} in {message.name} must fits the space alocated, the encoded value is {max_encoded} and the maximum value to this space is {total_size+negative_size} (its a signed int)")
                if( min_encoded < negative_size ):
                    header.write( "#error \"the minimum must fits the space alocated\" \n")
                    raise Exception(f"the minimum of {signal.name} in {message.name} must  fits the space alocated, the encoded value is {min_encoded} and the maximum value to this space is {negative_size} (its a signed int)")
            else:
                if( max_encoded > total_size ):
                    header.write( "#error \"the maximum must fits the space alocated\"\n")
                    raise Exception(f"the maximum of {signal.name} in {message.name} must fits the space alocated, the encoded value is {max_encoded} and the maximum value to this space is {total_size}")
                if(  min_encoded < 0  ):
                    header.write( "#error \"the minimum must be equals or larger than 0\"\n")
                    raise Exception(f"the minimum of {signal.name} in {message.name} must be equals or larger than 0, the encoded value is {min_encoded}")

            if signal.choices:
                header.write(f"// Named Values to Signal: {signal.name}\n")
                for named_value in signal.choices:
                    header.write(f"#define CAN_VALUE_{signal.choices[named_value]} CAN_VALUE_{signal.choices[named_value]}\n")
                    header.write(f"#define CAN_MSG_{message.name}_CAN_SIG_{signal.name}_CAN_VALUE_{signal.choices[named_value]} {named_value}\n")
            
            header.write("\n")



    header.write( "\n")
    header.write( "\n")
    header.write( "//arg _CAN_MSG: the name of the message with prefix CAN_MSG_ \n")
    header.write( "//arg _CAN_SIG: the name of the signal  with prefix CAN_SIG_ \n")
    header.write( "//arg _PAYLOAD: payload arrived in the CAN \n")
    header.write( "//return VALUE: value decoded \n")
    header.write( "\n")
    header.write( "#define CAN_SIG_DECODE( _CAN_MSG , _CAN_SIG , _PAYLOAD ) \\\n")
    header.write( "( ( ( _CAN_MSG##_t *) &_PAYLOAD )->_CAN_SIG ) * ( (float) _CAN_MSG##_##_CAN_SIG##_SCALE) + _CAN_MSG##_##_CAN_SIG##_OFFSET\n")
    header.write( "\n")
    header.write( "\n")
    header.write( "//arg _CAN_MSG: the name of the message with prefix CAN_MSG_ \n")
    header.write( "//arg _CAN_SIG: the name of the signal  with prefix CAN_SIG_ \n")
    header.write( "//arg _VALUE: the value to be encoded \n")
    header.write( "//return SIG_PAYLOAD: the value encoded \n")
    header.write( "\n")
    header.write( "#define CAN_SIG_ENCODE( _CAN_MSG , _CAN_SIG , _VALUE ) \\\n")
    header.write( "( _CAN_MSG##_##_CAN_SIG##_TRANSMISSION_TYPE ) ( ( _VALUE - _CAN_MSG##_##_CAN_SIG##_OFFSET)/( (float) _CAN_MSG##_##_CAN_SIG##_SCALE ) )\n")
    header.write( "\n")
    header.write( "\n")
    header.write( "//arg _CAN_MSG: the name of the message with prefix CAN_MSG_ \n")
    header.write( "//arg _CAN_SIG: the name of the signal  with prefix CAN_SIG_ \n")
    header.write( "//arg _VALUE: the value to be encoded \n")
    header.write( "//return IS_VALID: boolean informing if this value is valid\n")
    header.write( "\n")
    header.write( "#define CAN_SIG_IS_VALID( _CAN_MSG , _CAN_SIG , _VALUE ) \\\n")
    header.write( "( _CAN_MSG##_##_CAN_SIG##_MINIMUM <= _VALUE ) && ( _VALUE <= _CAN_MSG##_##_CAN_SIG##_MAXIMUM)\n")
    header.write( "\n")
    header.write( "\n")
    header.write( "//arg _CAN_MSG: the name of the message with prefix CAN_MSG_ \n")
    header.write( "//arg _CAN_SIG: the name of the signal  with prefix CAN_SIG_ \n")
    header.write( "//arg _CAN_VALUE: the name of the value with prefix CAN_VALUE \n")
    header.write( "//return VALUE: value of the named value\n")
    header.write( "\n")
    header.write( "#define CAN_GET_VALUE_BY_NAME( _CAN_MSG , _CAN_SIG , _CAN_VALUE ) \\\n")
    header.write( "( _CAN_MSG##_##_CAN_SIG##_##_CAN_VALUE )\n")