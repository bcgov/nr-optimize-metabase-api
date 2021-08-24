import sys
import constants


def main(argv):
    print(f"Bucket Name: {constants.BUCKET_NAME}")


if __name__ == "__main__":
    main(sys.argv[1:])
