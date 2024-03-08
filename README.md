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



## Funny Ones

List of weird, interesting, funny, or otherwise notable emails in the corpus

- [Interesting facts, Hmmmm](maildir/lenhart-m/sent/1521.)
- [Re: RESULTS OF MAN NIGHT](maildir/parks-j/inbox/646.)

- [Advice to Give Your Daughters](maildir/ring-a/sent/17.)
- [Re: Hey](maildir/guzman-m/discussion_threads/374.)
- [Fw: This Is the Captain Speaking](maildir/giron-d/sent/599.)

## Broken files

List of files with Unicode decode exceptions when opening the whole file as text. Note that these parse file with `email.BytesParser`

[maildir/kitchen-l/_americas/esvl/87.](maildir/kitchen-l/_americas/esvl/87.) has invalid email addresses in the `To` field

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

