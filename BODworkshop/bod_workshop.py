import os

# by LLCampos
def is_annotation_line(line):
    """Returns True if this line corresponds to a annotation line in the Webanno TSV file, False otherwise"""
    if line.strip().startswith('#') or line.strip() == '':
        return False
    return True

datadir = "data/" # "annotation"
refdir = "ref/" # "source"
crowddir = "final/" # annotations improved by crowd
users_list = ["user1", "user2", "user3", "user4", "user5", "user6", "user7",
              "user8", "user9", "user10",]
users = {} # user -> {agreement_score, new_annotations_score}
for u in users_list:
    users[u] = {"agreement_score": 0, "new_annotation_score": 0,
                "total_yes": 0, "total_no": 0}

def parse_corrections(datadir):
    docs = {} # doc -> annotation -> {votes: list users who voted on this radlex annotation
    #                                 yes: percentage of users of voted on this annotation
    #                                 no: percentage of users who did not vote on this annotation}

    # parse annotations to docs dictionary
    for subdir, dirs, files in os.walk(datadir):
        # print subdir, dirs, files
        docname = subdir.split("/")[-1]
        docs[docname] = {}
        for f in files:
            with open(os.path.join(subdir, f), 'r') as annots:
                for l in annots:
                    username = f.split(".")[0]
                    if is_annotation_line(l): # ignore all other annotations
                        values = l.split('\t')
                        if values[0] not in docs[docname]:
                            docs[docname][values[0]] = {"votes": [], "yes": 0, "no": 0}
                        if "RADLEX" in values[2]:
                            docs[docname][values[0]]["votes"].append(username)
        for i in docs[docname]:
            docs[docname][i]["yes"] = len(docs[docname][i]["votes"])*1.0/len(files)
            docs[docname][i]["no"] = 1 - docs[docname][i]["yes"]
    return docs

# for each token in ref data, assign scores to users
def rank_users(docs, users, refdir):
    for docname in os.listdir(refdir):
        with open(refdir + docname, 'r') as ref:
            for l in ref:
                if is_annotation_line(l):
                    values = l.split('\t')
                    tokenid = values[0]
                    tokenlabel = values[2]
                    for u in users:
                        if "RADLEX" in tokenlabel:
                            # user voted yes on a bioportal annotation
                            if u in docs[docname][tokenid]["votes"]:
                                users[u]["agreement_score"] += docs[docname][tokenid]["yes"]
                                users[u]["total_yes"] += 1
                            else:
                                users[u]["agreement_score"] += docs[docname][tokenid]["no"]
                                users[u]["total_no"] += 1
                        # user added a new annotation
                        elif u in docs[docname][tokenid]["votes"]:
                            users[u]["new_annotation_score"] += 1

    print "Bioportal annotations agreement"
    for s in sorted(users.iteritems(), key=lambda (x, y): y['agreement_score'], reverse=True):
        print s

    print "New annotation"
    for s in sorted(users.iteritems(), key=lambda (x, y): y['new_annotation_score'], reverse=True):
        print s

def write_crowd_corpus(docs, refdir, crowddir, threshold=0.8):
    for docname in os.listdir(refdir):
        crowdfile =  open(crowddir + "/" + docname, 'w')
        with open(refdir + docname, 'r') as ref:
            for l in ref:
                if is_annotation_line(l):
                    values = l.split('\t')
                    tokenid = values[0]
                    tokenlabel = values[2]
                    # ignore added annotations
                    if "RADLEX" not in tokenlabel or docs[docname][tokenid]["yes"] > threshold:
                        crowdfile.write("{}\t{}\t{}".format(tokenid, values[1], tokenlabel))
                    else:
                        crowdfile.write("{}\t{}\t{}".format(tokenid, values[1], "O\n"))
                else:
                    crowdfile.write(l)

#print users
docs = parse_corrections(datadir)
rank_users(docs, users, refdir)
write_crowd_corpus(docs, refdir, crowddir)
#pp.pprint(users)

