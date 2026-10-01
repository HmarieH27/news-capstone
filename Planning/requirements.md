# News application design

Readers register, log in, browse approved content and choose publisher/journalist
subscriptions. Journalists create and maintain their own drafts and newsletters.
Editors are assigned by an administrator; publisher editors manage that publisher's
articles and all editors may review independent articles. Readers cannot write.
Journalists cannot approve or edit another author's articles. Newsletter changes
are restricted to the author or an editor. Only approved articles enter newsletters.

The home page groups reading content and the editorial workspace. Forms show
validation errors, every mutation uses POST and CSRF, and approval delivery failures
leave a visible retry action. Token-authenticated APIs expose the required article
methods; the all-approved and subscription-filtered collections are separate routes.
The approval service emails subscribers individually and POSTs an authenticated
receipt to the application's own endpoint. Delivery state permits retries; crashes
can result in at-least-once email delivery, documented in README.

Relational tables use separate User, Publisher, Article, Newsletter, ApprovalLog and
ApprovalDelivery entities. Many-to-many join tables model memberships, subscriptions
and newsletter article selections, without comma-separated lists. Each non-key
attribute depends on its entity key; article authors and publishers are foreign
keys, not duplicated user/publisher details. Reverse user relations expose authored
articles and newsletters. Inapplicable reader subscriptions are empty join tables.

Non-functional requirements: readable PEP 8 Python, validated forms/serializers,
server-side ownership checks, hashed passwords, environment-based deployment
settings, finite HTTP timeouts, migrations and positive/negative permission tests.
MariaDB is supported and must be migrated and exercised before submission.
