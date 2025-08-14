import logging

# Buat File Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Buat Nama Handler
file_handler = logging.FileHandler("admin_info.log")
file_handler.setLevel(logging.INFO) # Only log INFO and higher to the file

# Buat Formatter lalu tambah ke file handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# tambah file handler ke logger
logger.addHandler(file_handler)

# Secara Opsional, lalu log ke konsol
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
# End Konfigurasi Logging
