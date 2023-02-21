from S3MPython import dm
from S3MPython import settings

def test_dm():
    # Test the dm module
    # Create a dm object
    print(f"S3MPython version: {settings.VERSION}")
    dm1 = dm.DMType('DM1 Title')
    # Set the dm object's parameters
    dm1.description = 'This is a test dm object'
    dm1.author = 'S3MPython'
    dm1.version = '1.0'
    dm1.date = '2018-01-01'
    dm1.time = '00:00:00'
    dm1.time_zone = 'UTC'
    return dm1

if __name__ == '__main__':

    dm1 = test_dm()
    print(dm1)
    print(f"Creator: {dm1.md_creator}")
    dm1.md_creator = 'Me again'
    print(f"Edited Creator: {dm1.md_creator}")

