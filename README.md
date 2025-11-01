# enron-corpus
Repo of various utilities for interacting with the Enron email corpus

## Initial Setup

Download the corpus tar.gz:
```
wget https://www.cs.cmu.edu/~enron/enron_mail_20150507.tar.gz
```

Unzip:

```
tar -xzf enron_mail_20150507.tar.gz
```

Make the files read-only (optional):

```
chmod -R -w maildir/
```

Parse the emails and store them in a Parquet file and SQL database
```
python import_emails.py
```

## Running the viewer

Flask + Parquet:
```
python flask_app.py
```


## Saved Emails

My list of weird, interesting, funny, or otherwise notable emails in the corpus

- [Interesting facts, Hmmmm](maildir/lenhart-m/sent/1521.)
- [Re: RESULTS OF MAN NIGHT](maildir/parks-j/inbox/646.)
- [Advice to Give Your Daughters](maildir/ring-a/sent/17.)
- [Re: Hey](maildir/guzman-m/discussion_threads/374.)
- [Fw: This Is the Captain Speaking](maildir/giron-d/sent/599.)
- [Holiday Party - Canceled](maildir/germany-c/deleted_items/311.)
- [RE: Thanksgiving](maildir/tholt-j/sent_items/273.)
- [RE: (no subject)](maildir/maggi-m/deleted_items/481.)
- [FW: (no subject)](maildir/buy-r/sent_items/98.)
- [FW: My life](maildir/tycholiz-b/deleted_items/125.)
- [Cuntry-Girls](maildir/campbell-l/all_documents/634.)
- [Mike's Quotation](maildir/mann-k/inbox/242.)
- [RE: Reply Requested: Do You Code Or Approve Invoices?](maildir/hain-m/notes_inbox/261.)
- [FW: ready for the next hunt](maildir/donohoe-t/sent_items/14.)
- [RE: Jesse](maildir/lenhart-m/sent_items/819.) 
- [FW: Things you'll never hear women say.](maildir/whitt-m/inbox/447.)
- [SEC Information/Earnings Restatement](maildir/rogers-b/trading_info/76.)
- [FW: DAVE BARRY](maildir/kaminski-v/discussion_threads/367.)
- [World's Thinnest Books](maildir/nemec-g/sent/13.)
- [!!!!!!!!!!!GONE.SCR VIRUS Warning!!!!!!!!!!!11](maildir/salisbury-h/inbox/194.)
- [FW: Tavel advisory:  France - I thought you and Jim might like this](maildir/kean-s/sent_items/105.)
- [Yesterdays sermon](maildir/donohoe-t/sent_items/9.)
- [Re: houston, we have a problem....?](maildir/scott-s/sent/669.)
- [h:\ drive](maildir/storey-g/deleted_items/162.)
- [Re: halloween](maildir/lucci-p/deleted_items/78.)
- [Halloween](maildir/mcconnell-m/inbox/15.)
- [FW: Humor](maildir/germany-c/inbox/29.)
- [(no subject)](maildir/lenhart-m/deleted_items/414.)
- [FW: Spontaneous Combustion](maildir/williams-w3/symesees/71.)
- [Suggestions to help short term morale](maildir/beck-s/inbox/483.)
- [RE:](maildir/richey-c/personal/2.)
- [RE:](maildir/richey-c/sent_items/234.)
- [RE: What happened...](maildir/richey-c/sent_items/221.)
- [RE:](maildir/richey-c/sent_items/193.)
- [not a bad way to go](maildir/bass-e/deleted_items/39.)
- [Absolutely the best cat story I have ever heard](maildir/donoho-l/inbox/junk_file/104.)
- [RE: dream](maildir/stokley-c/chris_stokley/sent/121.)
- [Is there pornography on your computer? FREE System Check](maildir/mims-thurston-p/deleted_items/92.)
- [Re: Child Labor](maildir/cash-m/sent_items/231.)
- [FW: New Math](maildir/shackleton-s/deleted_items/571.)
- [you can appreciate this](maildir/hyatt-k/sent_items/188.)
- [FW: i luv this one](maildir/lokey-t/sent_items/139.)
- [FW: quite amusing....](maildir/hyatt-k/deleted_items/370.)
- [FW: The Real Story on Enron...](maildir/shackleton-s/inbox/678.)
- [Corn Pudding](maildir/white-s/inbox/205.)
- [(no subject)](maildir/lay-k/inbox/888.)
- [RE: KILL!](maildir/parks-j/sent_items/753.)
- [FW: FW: Chili contest](maildir/white-s/inbox/128.)
- [Thank you and Stay Strong](maildir/lay-k/inbox/309.)
- [Re:  Jeff's Leaving](maildir/lay-k/sent_items/6.)
- [LJM/Raptor valuations](maildir/buy-r/inbox/1076.)
  - [FW: Raptors](maildir/kaminski-v/inbox/92.)
- [FW: Text of Letter to Enron's Chairman After Departure of Chief Executive](maildir/dorland-c/deleted_items/140.)
- [FW: FW: Do this, it's hilarious!](maildir/lenhart-m/sent_items/339.)
- [Fwd: FW: Children's Books You'll NEVER See!](maildir/lenhart-m/discussion_threads/203.)
- [FW: ONE WEEK till Pajama Pub Crawl](maildir/lenhart-m/all_documents/1587.)
- [Fwd: Fw: Click on the link and see what happens](maildir/lenhart-m/discussion_threads/361.)
  - https://web.archive.org/web/20001018153603/http://home.att.net/~viseguy/fun.html
- [Re: The 9th Friday State of the Union](maildir/lenhart-m/sent_items/51.)
- [Re: FW: Prison Bitch Name Generator](maildir/lenhart-m/discussion_threads/143.)
  - https://web.archive.org/web/20040401184701/http://members.iglou.com:80/lyons/bitchGen.html
- [something groovy fr. the Dali Lama](maildir/lenhart-m/sent_items/66.)
- [RE: the atmosphere at this](maildir/lenhart-m/sent_items/822.)
- [FW: guide](maildir/dorland-c/sent_items/364.)
- [FW: Painting in the Nude](maildir/baughman-d/deleted_items/211.)

- leads to chase:
  - maildir/lenhart-m/sent_items/504.
    - participant: richardson@sarofim.com
  - FROM:   matthew.lenhart@enron.com 
    TO:    chad.landry@enron.com


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