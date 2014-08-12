# -*- coding: utf-8 -*-

from __future__ import absolute_import
from vilya.libs.store import OrzField, store, IntegrityError, OrzBase
from vilya.libs.props import PropsItem，
from vilya.libs.doubandb import db as bdb
from vilya.models.consts import DOMAIN
from vilya.models.git.repo import ProjectRepo
from vilya.models.project import Project
from vilya.models.ticket.ticket import Ticket

MCKEY_TICKET = 'ticket:%s'
BDB_TICKET_DESCRIPTION_KEY = 'ticket_description:%s'
BDB_TICKET_COMMENT_CONTENT_KEY = 'ticket_comment_content:%s'
BDB_TICKET_LINECOMMENT_CONTENT_KEY = 'ticket_linecomment_content:%s'
PULL_COMMENT_UID_PATTERN = ''

class TicketNode(object):

    (
        TICKET_NODE_TYPE_OPEN,
        TICKET_NODE_TYPE_CLOSE,
        TICKET_NODE_TYPE_MERGE,
        TICKET_NODE_TYPE_COMMIT,
        TICKET_NODE_TYPE_COMMENT,
        TICKET_NODE_TYPE_CODEREVIEW, # deprecated
        TICKET_NODE_TYPE_LINECOMMENT,
    ) = range(7)


class TicketCommits(OrzBase, TicketNode):
    __orz_table__ = "ticket_commits"
    ticket_id = OrzField(as_key=OrzField.KeyType.DESC)
    commits = OrzField()
    author = OrzField()
    time = OrzField()

    @property
    def ticket(self):
        return Ticket.get(self.ticket_id)

    @property
    def project(self):
        return Project.get(self.ticket.project_id)


    @classmethod
    def commit_as_dict(cls, proj, sha):
        d = {}
        d['sha'] = sha
        commit = proj.repo.get_commit(sha)
        d['commit'] = commit.as_dict()
        parent = [dict(sha=commit.parent,
                       html_url="%s/%s/commits/%s" % (DOMAIN, proj.name, commit.parent))
                  ] if commit.parent else []
        d['parent'] = parent

        return d

    def as_dict(self):
        l = []
        for sha in self.commits.split(','):
            d = TicketCommits.commit_as_dict(self.project, sha)
            l.append(d)
        return l

    @classmethod
    def add(cls, **kw):
        tn = None
        try:
            tn = cls.create(**kw)
        except IntegrityError:
            store.rollback()
        return tn

    @classmethod
    def gets_by_ticketid(cls, ticket_id):
        rs = cls.gets_by(ticket_id=ticket_id)
        return rs[0] if rs else None


class TicketComment(OrzBase, object):
    __orz_table__ = "ticket_comments"
    ticket_id = OrzField(as_key=OrzField.KeyType.DESC)
    author = OrzField()
    time = OrzField()

    content = PropsItem('content', default='', output_filter=str)

    @property
    def uid(self):
        return PULL_COMMENT_UID_PATTERN % self.id

    def as_dict(self):
        return {
            'content': self.content,
            'author': self.author,
            'date': self.time.strftime('%Y-%m-%dT%H:%M:%S'),
            'id': self.id,
            'ticket_id': self.ticket_id
        }

    @classmethod
    def add(cls, **kw):
        ticket_id = kw['ticket_id']
        content = kw['content']
        author = kw['author']
        bdb.set(BDB_TICKET_COMMENT_CONTENT_KEY % id, content)
        tc = None
        try:
            tc = cls.create(**kw)
        except IntegrityError:
            store.rollback()
        return tc

    def update(self, content):
        # update time
        #

        bdb.set(BDB_TICKET_COMMENT_CONTENT_KEY % self.id, content)

    def delete(self):
        node = TicketNode.get_by_comment(self)
        if node:
            node.delete()
        bdb.delete(BDB_TICKET_COMMENT_CONTENT_KEY % self.id)
        n = store.execute("delete from codedouban_ticket_comment "
                          "where id=%s", self.id)
        if n:
            store.commit()
            return True

    @classmethod
    def get(cls, id):
        # cls.get
        ### with content set
        pass


    @classmethod
    def gets_by_ticketid(cls, ticket_id):
        rs = cls.gets_by(ticket_id=ticket_id)
        return rs[0] if rs else None
