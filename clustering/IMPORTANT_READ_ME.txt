Dealing with BST is a pain in the neck. In the raw N2EX data, the hour at which the day starts moves in the summer. For this analysis I have redone the index so that the day always starts at 23:00. I have also deleted the extra hour from the 25hr day in the autumn, and added a row to the 23h day in the spring.
The script may then take the data 24 rows at a time and always have e.g. the 7th row corresponding to 05:00-06:00 on the clock.

This is different to the way Sam's data is strcutured, as he leaves the 23h and 25h days in the table.
