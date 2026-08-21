from toolz import *  # noqa: F403


def stem(word):
    """Stem word to primitive form"""
    return word.lower().rstrip(",.!:;'-\"").lstrip("'\"")


wordcount = comp(frequencies, partial(map, stem), str.split)  # noqa: F405

if __name__ == "__main__":
    print(wordcount("This cat jumped over this other cat!"))
    # prints {'this': 2, 'cat': 2, 'jumped': 1, 'over': 1, 'other': 1}
