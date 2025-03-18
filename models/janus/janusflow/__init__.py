#  Copyright (c) 2025. Salim Janji. All rights reserved.
#  Unauthorized copying, distribution, or modification of this file is strictly prohibited.

#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
#
# check if python version is above 3.10
import sys

if sys.version_info >= (3, 10):
    print("Python version is above 3.10, patching the collections module.")
    # Monkey patch collections
    import collections
    import collections.abc

    for type_name in collections.abc.__all__:
        setattr(collections, type_name, getattr(collections.abc, type_name))
