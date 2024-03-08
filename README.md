# enron-corpus
Repo of various utilities for interacting with the Enron email corpus



To unzip the corpus:

```
tar -xvzf enron_mail_20150507.tar.gz
```

Make the files read-only (optional):

```
chmod -R -w maildir/
```

## Hard to parse ones

```
maildir/sager-e/all_documents/2059.
maildir/kean-s/archiving/untitled/5745.
```



## Saved Emails

List of weird, interesting, funny, or otherwise notable emails in the corpus

- [Interesting facts, Hmmmm](maildir/lenhart-m/sent/1521.)
- [Re: RESULTS OF MAN NIGHT](maildir/parks-j/inbox/646.)
- [Advice to Give Your Daughters](maildir/ring-a/sent/17.)
- [Re: Hey](maildir/guzman-m/discussion_threads/374.)
- [Fw: This Is the Captain Speaking](maildir/giron-d/sent/599.)
- [Holiday Party - Canceled](maildir/germany-c/deleted_items/311.)
- [RE: Thanksgiving](maildir/tholt-j/sent_items/273.)

## Broken files

List of files with invalid email addresses in the `To` header, causing an exception during parsing. The invalid email addresses appear to be ones that start with a period, such as `.flood@enron.com`  or `.costa@enron.com` 

```
maildir/kitchen-l/_americas/esvl/87.
maildir/kitchen-l/_americas/netco_restart/3.
maildir/kitchen-l/_americas/netco_eol/82.
maildir/kitchen-l/_americas/netco_eol/83.
maildir/kitchen-l/sent_items/24.
```

List of files with Unicode decode exceptions when opening the whole file as text with `mode='r'`. These files parse correctly when using `email.BytesParser` and opening the file with `mode='rb'`

```
maildir/whalley-g/inbox/390.
maildir/whalley-g/inbox/60.
maildir/ybarbo-p/deleted_items/90.
maildir/ybarbo-p/deleted_items/91.
maildir/ybarbo-p/deleted_items/83.
maildir/ybarbo-p/inbox/271.
maildir/ybarbo-p/inbox/232.
maildir/ybarbo-p/inbox/276.
maildir/ybarbo-p/inbox/163.
maildir/gay-r/all_documents/82.
maildir/gay-r/all_documents/59.
maildir/gay-r/sent/82.
maildir/gay-r/sent/59.
maildir/griffith-j/deleted_items/1175.
maildir/griffith-j/all_documents/565.
maildir/griffith-j/design/27.
maildir/griffith-j/discussion_threads/535.
maildir/griffith-j/inbox/66.
maildir/shackleton-s/all_documents/2374.
maildir/shackleton-s/all_documents/1560.
maildir/shackleton-s/all_documents/2856.
maildir/shackleton-s/notes_inbox/1701.
maildir/shackleton-s/notes_inbox/1491.
maildir/shackleton-s/stack__shari/3.
maildir/campbell-l/all_documents/1014.
maildir/campbell-l/discussion_threads/889.
maildir/campbell-l/notes_inbox/284.
maildir/quigley-d/myfriends/142.
maildir/quigley-d/myfriends/44.
maildir/lay-k/inbox/533.
maildir/lay-k/inbox/15.
maildir/lay-k/inbox/333.
maildir/causholli-m/deleted_items/55.
maildir/causholli-m/deleted_items/405.
maildir/kean-s/california___working_group/163.
maildir/kitchen-l/_americas/regulatory/113.
maildir/shapiro-r/deleted_items/221.
maildir/dasovich-j/all_documents/29349.
maildir/dasovich-j/notes_inbox/11527.
maildir/ring-a/inbox/9.
maildir/hyatt-k/personal/cars/6.
maildir/shankman-j/deleted_items/510.
maildir/shankman-j/personal/12.
maildir/shankman-j/saved_mail/1.
maildir/beck-s/deleted_items/353.
maildir/beck-s/deleted_items/13.
maildir/beck-s/deleted_items/91.
maildir/beck-s/deleted_items/85.
maildir/beck-s/deleted_items/48.
maildir/beck-s/deleted_items/36.
maildir/beck-s/deleted_items/264.
maildir/beck-s/deleted_items/38.
maildir/beck-s/deleted_items/299.
maildir/beck-s/inbox/504.
maildir/beck-s/inbox/704.
maildir/beck-s/inbox/708.
maildir/beck-s/inbox/100.
maildir/beck-s/inbox/763.
maildir/staab-t/personal/17.
maildir/skilling-j/deleted_items/346.
maildir/skilling-j/all_documents/385.
maildir/skilling-j/discussion_threads/306.
maildir/skilling-j/notes_inbox/100.
maildir/buy-r/deleted_items/84.
maildir/sanders-r/bastos/4.
maildir/sanders-r/deleted_items/bastos/4.
maildir/sanders-r/all_documents/7334.
maildir/sanders-r/all_documents/7342.
maildir/sanders-r/all_documents/7328.
maildir/sanders-r/notes_inbox/315.
maildir/sanders-r/notes_inbox/313.
maildir/sanders-r/notes_inbox/312.
maildir/kaminski-v/sent_items/2524.
maildir/haedicke-m/all_documents/2313.
maildir/haedicke-m/notes_inbox/344.
maildir/haedicke-m/inbox/594.
maildir/taylor-m/all_documents/7852.
maildir/taylor-m/all_documents/3452.
maildir/taylor-m/all_documents/2813.
maildir/taylor-m/all_documents/3474.
maildir/taylor-m/notes_inbox/2425.
maildir/taylor-m/notes_inbox/1149.
maildir/taylor-m/notes_inbox/1606.
maildir/taylor-m/notes_inbox/1591.
maildir/taylor-m/inbox/social/73.
maildir/taylor-m/archive/8_00/32.
maildir/horton-s/all_documents/209.
maildir/horton-s/all_documents/64.
maildir/horton-s/discussion_threads/60.
maildir/horton-s/discussion_threads/198.
```

## Enron Collapse Timeline

Source: https://www.famous-trials.com/enron/1789-chronology

| Date                 | Event                                                        |
| -------------------- | ------------------------------------------------------------ |
| 1985                 | Enron is founded by Ken Lay after merging Houston Natural Gas and InterNorth. |
| August 1, 1990       | Jeffrey Skilling assumes job as chairman and chief executive of Enron Finance. |
| December 3, 1990     | Andy Fastow is hired by Skilling for a position in Enron's new finance business |
| January 30, 1992     | The SEC allows Enron to use mark-to market accounting instead of traditional, accrual accounting. The new accounting system allows Enron to begin reporting fast-growing profits. |
| 1992                 | Enron becomes the largest seller of natural gas in North America. |
| 1999                 | Chief Financial Officer Andy Fastow forms two limited partnerships, LJM Cayman and LJM2 for the purpose of buying Enron's poorly assets. Fastow receives an exemption from conflict-of-interest rules by the Board of Directors, thus allowing him to manage the companies. |
| July 2000            | Enron and Blockbuster enter into a 20-year agreement to stream on-demand video entertainment. Enron claims $110 million in profits from the deal, even though the network would fail and Blockbuster withdraws from the contract. |
| August 23, 2000      | Enron stock its an all-time price high of $90 a share.       |
| September 6, 2000    | Andy Fastow and CAO Richard Causey meet to discuss the "Global Galactic" agreement that protects Fastow from losses in the side deals he has made for Enron with LJM. |
| December 31, 2000    | Enron finishes the tear with its stock price up 87% to $83.13, 70 times earnings. Fortune magazine calls it the most innovative large company in the United States. |
| March 5, 2001        | Bethany McLean publishes an article *Is Enron Overpriced?* in Fortune magazine. She writes that investors are generally clueless as to how Enron earns its reported profits. |
| April 17, 2001       | Skilling verbally attacks an analyst who questions Enron's failure to release a balance sheet along with its earnings statements, calling the an "asshole." |
| **August 14, 2001**  | Skilling resigns as CEO of Enron. Lay re-assumes the job as CEO. |
| August 15, 2001      | Vice president for development at Enron, Sherron Watkins, sends an anonymous letter to Lay criticizing the company's accounting practices. In the letter she says she is worried Enron "will implode in a wave of accounting scandals." |
| August 22, 2001      | Watkins meets with Lay and gives him a 6-page letter detailing problems with Enron's accounting practices. Lay promises to take her concerns to the company's law firm, Vinson & Ellis. |
| September 9, 2001    | A manager of an important hedge fund says "Enron stock is trading under a cloud" as its stock price continues to fall. |
| October 16, 2001     | Enron announces that it will have to restate its earnings from 1997 to 2000 to correct accounting violations. |
| October 22, 2001     | The Enron Board learns that Fastow received $30 million (more, actually) from managing LJM partnerships. Enron's stock drops 20% in a day after the SEC announces that it will investigate several Enron deals. |
| October 24, 2001     | Enron fires Andy Fastow.                                     |
| October 30, 2001     | Credit rating agencies lower Enron's credit rating. From August through the end of October, Ken Lay has sold 918,000 shares of Enron while insisting to others the company was in good financial shape. |
| November 2001        | In a desperate effort to save itself from bankruptcy, Enron explores merger or acquisition possibilities with rival Dynegy. |
| November 28, 2001    | Dynegy says it will not acquire Enron. Enron's credit rating is reduced to junk status. Enron's stock price falls to $0.61. |
| **December 2, 2001** | Enron seeks Chapter 11 bankruptcy protection.                |
| December 2001        | Skilling tells the *New York Times* , "I had no idea that the compay was in anything but excellent shape." |
| January 23, 2002     | Ken lay resigns as Enron's chairman and CEO.                 |
| February 7, 2002     | Skilling testifies before about the Enron collapse before a congressional committee; Fastow invokes his 5th Amendment protection and refuses to testify. |
| June 15, 2002        | Enron's auditing firm, Arthur Andersen, is convicted of obstruction of justice in connection with its shredding of Enron documents. |
| July 30, 2002        | President George W. Bush signs the Sarbanes-Oxley Act imposing new accounting and reporting obligations on American businesses. |
| August 31, 2002      | Enron accounting firm Arthur Andersen surrenders its CPA license and its 85,000 employees lose their jobs. |
| October 31, 2002     | Andy Fastow is indicted on 78 counts of fraudulent conduct.  |
| May 1, 2003          | Lea Fastow, the wife of Andy Fastow, is charged with conspiracy and tax evasion. |
| January 14, 2004     | Andy Fastow enters into a plea agreement and promises to cooperate in the prosecution of other Enron executives. |
| February 18, 2004    | A grand jury in Houston indicts Jeff Skilling on 35 counts, including charges of fraud, insider trading, and conspiracy. |
| July 7, 2004         | A grand jury indicts Ken Lay on 11 counts, including charges of wire fraud, securities fraud, bank fraud, and conspiracy. The next day, Lay surrenders to the FBI. |
| December 28, 2005    | Richard Causey enters into a plea bargain agreement with the government. |
| January 30, 2006     | Jury selection begins in the trial of Lay and Skilling.      |
| May 17, 2006         | The jury begins deliberation in the trial of Lay and Skilling. |
| May 25, 2006         | The jury convicts Skilling of 19 of 28 counts of wire fraud and securities fraud. Lay is convicted on all six counts of fraud. |
| July 5, 2006         | While staying in a cabin outside Aspen, Colorado with his wife, Ken Lay suffers a heart attack and dies. |
| September 26, 2006   | Andy Fatow is sentenced to six years in prison.              |
| October 23, 2006     | Judge Lakes sentences Skilling to 24 years in prison and sets a fine of $45 million. |
| December 13, 2006    | Jeff Skilling begins serving his sentence in a low-security prison in Waseca, Minnesota. |
| December 16, 2011    | Andy Fastow is released from prison.                         |
| June 21, 2013        | Judge Lake reduces Skilling's sentence to 14 years (and, with good-time credits, he could be released by 2017). |