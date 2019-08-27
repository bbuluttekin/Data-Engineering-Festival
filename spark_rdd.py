def count_elements_in_dataset(dataset):
    """
    Given a dataset loaded on Spark, return the
    number of elements.
    :param dataset: dataset loaded in Spark context
    :type dataset: a Spark RDD
    :return: number of elements in the RDD
    """

    return dataset.count()


def get_first_element(dataset):
    """
    Given a dataset loaded on Spark, return the
    first element
    :param dataset: dataset loaded in Spark context
    :type dataset: a Spark RDD
    :return: the first element of the RDD
    """

    return dataset.first()


def get_all_attributes(dataset):
    """
    Each element is a dictionary of attributes and their values for a post.
    Can you find the set of all attributes used throughout the RDD?
    The function dictionary.keys() gives you the list of attributes of a dictionary.
    :param dataset: dataset loaded in Spark context
    :type dataset: a Spark RDD
    :return: all unique attributes collected in a list
    """

    return dataset.flatMap(lambda x: x.keys()).distinct().collect()


def get_elements_w_same_attributes(dataset):
    """
    We see that there are more attributes than just the one used in the first element.
    This function should return all elements that have the same attributes
    as the first element.

    :param dataset: dataset loaded in Spark context
    :type dataset: a Spark RDD
    :return: an RDD containing only elements with same attributes as the
    first element
    """
    def check(first_item, item):
        first_attr = set(first_item.keys())
        item_attr = set(item.keys())
        return first_attr == item_attr

    first_item = dataset.first()

    return dataset.filter(lambda x: check(first_item, x))


def get_min_max_timestamps(dataset):
    """
    Find the minimum and maximum timestamp in the dataset
    :param dataset: dataset loaded in Spark context
    :type dataset: a Spark RDD
    :return: min and max timestamp in a tuple object
    :rtype: tuple
    """
    from datetime import datetime as dt

    def extract_time(timestamp):
        return dt.utcfromtimestamp(timestamp)

    min_tstamp = dataset.map(lambda x: x['created_at_i']).reduce(
        lambda x, y: x if x < y else y)
    max_tstamp = dataset.map(lambda x: x['created_at_i']).reduce(
        lambda x, y: x if x > y else y)

    return extract_time(min_tstamp), extract_time(max_tstamp)


def get_number_of_posts_per_bucket(dataset, min_time, max_time):
    """
    Using the `get_bucket` function defined in the notebook (redefine it in this file), this function should return a
    new RDD that contains the number of elements that fall within each bucket.
    :param dataset: dataset loaded in Spark context
    :type dataset: a Spark RDD
    :param min_time: Minimum time to consider for buckets (datetime format)
    :param max_time: Maximum time to consider for buckets (datetime format)
    :return: an RDD with number of elements per bucket
    """
    def get_bucket(rec, min_timestamp, max_timestamp):
        interval = (max_timestamp - min_timestamp + 1) / 200.0
        return int((rec['created_at_i'] - min_timestamp)/interval)

    min_time = min_time.timestamp()
    max_time = max_time.timestamp()
    rdd = dataset.map(lambda x: (get_bucket(x, min_time, max_time), 1)
                      ).reduceByKey(lambda x, y: x + y)

    return rdd


def get_number_of_posts_per_hour(dataset):
    """
    Using the `get_hour` function defined in the notebook (redefine it in this file), this function should return a
    new RDD that contains the number of elements per hour.
    :param dataset: dataset loaded in Spark context
    :type dataset: a Spark RDD
    :return: an RDD with number of elements per hour
    """
    from datetime import datetime as dt

    def get_hour(rec):
        time = dt.utcfromtimestamp(rec['created_at_i'])
        return time.hour

    return dataset.map(lambda x: (get_hour(x), 1)).reduceByKey(lambda x, y: x+y)


def get_score_per_hour(dataset):
    """
    The number of points scored by a post is under the attribute `points`.
    Use it to compute the average score received by submissions for each hour.
    :param dataset: dataset loaded in Spark context
    :type dataset: a Spark RDD
    :return: an RDD with average score per hour
    """
    from datetime import datetime as dt

    def get_hour(rec):
        time = dt.utcfromtimestamp(rec['created_at_i'])
        return time.hour

    scores_rdd = dataset.map(lambda x: (get_hour(x), (x['points'], 1))).reduceByKey(
        lambda x, y: (x[0] + y[0], x[1] + y[1])).map(lambda x: (x[0], x[1][0] / x[1][1]))

    return scores_rdd


def get_proportion_of_scores(dataset):
    """
    It may be more useful to look at successful posts that get over 200 points.
    Find the proportion of posts that get above 200 points per hour.
    :param dataset: dataset loaded in Spark context
    :type dataset: a Spark RDD
    :return: an RDD with the proportion of scores over 200 per hour
    """
    from datetime import datetime as dt

    def get_hour(rec):
        time = dt.utcfromtimestamp(rec['created_at_i'])
        return time.hour

    prop_per_hour_rdd = dataset.map(
        lambda x: (get_hour(x), (1 if x['points'] > 200 else 0, 1))).reduceByKey(
            lambda x, y: (x[0] + y[0], x[1] + y[1])).map(
                lambda x: (x[0], x[1][0] / x[1][1]))

    return prop_per_hour_rdd


def get_proportion_of_success(dataset):
    """
    Using the `get_words` function defined in the notebook to count the
    number of words in the title of each post, look at the proportion
    of successful posts for each title length.

    Note: If an entry in the dataset does not have a title, it should
    be counted as a length of 0.

    :param dataset: dataset loaded in Spark context
    :type dataset: a Spark RDD
    :return: an RDD with the proportion of successful post per title length
    """
    import re

    def get_words(line):
        return re.compile(r'\w+').findall(line)

    prop_per_title_length_rdd = dataset.map(
        lambda x: (len(get_words(
            x.get('title', ''))), (1 if x['points'] > 200 else 0, 1))).reduceByKey(
                lambda x, y: (x[0] + y[0], x[1] + y[1])).map(
                    lambda x: (x[0], x[1][0] / x[1][1]))

    return prop_per_title_length_rdd


def get_title_length_distribution(dataset):
    """
    Count for each title length the number of submissions with that length.

    Note: If an entry in the dataset does not have a title, it should
    be counted as a length of 0.

    :param dataset: dataset loaded in Spark context
    :type dataset: a Spark RDD
    :return: an RDD with the number of submissions per title length
    """
    import re

    def get_words(line):
        return re.compile(r'\w+').findall(line)

    submissions_per_length_rdd = dataset.map(
        lambda x: (len(get_words(x.get('title', ''))), 1)).reduceByKey(
            lambda x, y: x + y)

    return submissions_per_length_rdd
