def normalize(original_name):
    match original_name.lower():
        case "test":
            return "Test_Normalized"
        case _:
            return "No Normalization!"