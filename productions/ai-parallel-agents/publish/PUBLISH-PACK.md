# Publish pack: 4 projects at once with Claude Code + Codex, and the switch-provider skill

Videos: long-landscape.mp4 (4:43, 16:9) and short-portrait.mp4 (1:17, 9:16)
Thumbnails: thumbnail-long-A.png, thumbnail-long-B.png, thumbnail-long-C.png, thumbnail-short.png

Replace [LONG VIDEO LINK] with the YouTube link of the long video after it goes live.


==================== PLATFORM RESEARCH (what each platform rewards, and how this pack uses it) ====================

YOUTUBE (long video)
- Title limit is 100 characters, but search and suggested feeds cut it at roughly 60 to 70. Every title below puts the search phrase in the first 50 characters.
- The description allows 5,000 characters. Only the first 150 to 200 show in search and above the fold, so the first two lines carry the main keywords: Claude Code, Codex, multiple projects, usage limit.
- Chapters starting at 0:00 with descriptive names show in the player and can show in Google results.
- Up to 15 hashtags are read, and up to 3 show above the title. This pack uses 3.
- The tags field allows 500 characters and plays a small role. It is used for spelling variants (cluade code, claude-code) and close phrases.
- YouTube also reads what is said and shown in the video. The narration already says Claude Code, Codex, usage limit, OpenRouter and switch-provider.

YOUTUBE SHORTS
- The title is the strongest text signal for Shorts search, with the keyword in the first few words. Keep it short (around 40 to 60 characters visible).
- The description stays short: one keyword sentence, the value, a link to the long video, then #shorts plus a few niche hashtags.
- Completion and rewatch drive distribution. The short loops back to the question it opens with.

LINKEDIN
- Native video uploads get better distribution than YouTube links, so upload the MP4 directly.
- The first two lines show before "see more" and decide whether people expand. They have to be a complete hook on their own.
- Dwell time and thoughtful comments (longer than a few words) weigh more than likes. The post ends with a real question that invites a detailed answer.
- Links in the post body may reduce reach. Sources disagree on how much, so the link goes in the first comment.
- 3 to 5 hashtags at most. Hashtags matter little.

FACEBOOK (long video)
- Facebook rewards video, and captions that read like a person talking. Long, conversational captions ending in a question do well.
- Title and description show in Facebook search. Video tags (up to 8, typed in the upload screen) help categorise the video.
- Early comments in the first 30 to 60 minutes matter. Reply quickly.
- 3 to 5 relevant hashtags. Off-topic or excessive hashtags reduce reach.

INSTAGRAM + FACEBOOK REELS (short video)
- Since December 2025, Instagram allows a maximum of 5 hashtags per Reel or post. The caption below uses exactly 5.
- Instagram indexes caption keywords for search, and keywords now matter more than hashtags. The first line holds the main search phrase.
- Sends (shares in DMs) and watch time are among the strongest Reel signals. The caption gives people a reason to send it to someone.
- Captions are limited to 2,200 characters. Only about the first 125 show before "more".
- When the same Reel goes to Facebook, the Facebook copy can be a bit more conversational. The block below works on both. Add the Facebook Reel tags from the tag block.
- On-screen text and spoken words are read for search. Use the cover text and keywords listed below.

TIKTOK (short video)
- TikTok is a search engine for many users. Captions, spoken words and on-screen text are all indexed.
- The search phrase goes at the very start of the caption. Only about 80 to 150 characters show before "more".
- Caption length limits are reported as 2,200 or 4,000 characters, so this caption stays under 2,200 to be safe.
- Long-tail phrases ("claude code usage limit", "how to use claude code and codex") beat broad words ("coding").
- Hashtags are mostly used for categorising, not reach. Use 3 to 5 specific ones.
- The first 1 to 3 seconds decide distribution. The opening on-screen text must state the outcome.

X (TWITTER)
- Free accounts get 280 characters per post. The main post below stays under 280.
- Posts with external links get less reach, so the link goes in the first reply.
- Native video gets more reach than a YouTube link, so upload the short MP4 directly.
- Replies and conversation weigh heavily. The post makes a clear claim people want to answer.
- Hashtags are optional. One at most.


==================== LINKEDIN POST (upload long-landscape.mp4 natively) (copy this block) ====================

I run four software projects at the same time with AI coding agents.

The hardest part is not the code. It is the moment an agent hits its usage limit halfway through a task.

Most developers think the limit is the problem. It isn't. The real cost is context: what was decided, what changed, what was tested and what is left. Lose that, and the next session starts from zero. You spend the first twenty minutes explaining everything again, and the agent still guesses wrong.

Here is the system I use every day.

1. Four VS Code windows, one project in each
Two run Claude Code and two run Codex. I give window one a clear task, move to window two while it works, then three, then four. When I come back to window one, finished work is waiting for review. The agents write, run and test. I plan, review and decide.

2. Six documents every agent reads before it starts
Requirements: what we are building and why
Architecture: the stack, the structure and the data flow
Design: colours, type and components
Memory: the current state and the next steps
Rules: commands and conventions (CLAUDE.md and AGENTS.md)
Tracker: every task, its status and its evidence

Most AI mistakes come from guessing. Written decisions remove the guessing.

3. A handoff skill for when the limit hits
I built a skill called switch-provider. It works the same way in Claude Code and Codex. When I run it, the agent:
- Finishes the smallest safe checkpoint, with no half-written changes and no commit just to switch
- Writes a structured handoff: goal, constraints, decisions, changed files, the tests that actually ran and their results, failures, blockers and the next action
- Never reports a test as passed if it did not run
- Saves the handoff to a private, git-ignored memory folder and records the git state
- Scans it for keys and tokens, and rejects it until anything sensitive is removed

Then I type /exit and the launcher asks me to choose between my subscription and OpenRouter, which runs on an API key with a spending cap I set myself. The agent never picks the provider, spends credit or changes credentials on its own.

The new session reads the handoff and continues from the same point. It is not a replay of the old chat. It is a written handover, and that is exactly why it is reliable.

An unexpected side effect: these handoff notes became the best documentation in every project. They are written for a reader with no memory, so any developer joining later can follow them too.

Speed in the AI era is not about typing faster. It is about using these tools with structure.

The full 5-minute breakdown is in the video above.

How do you keep context when an AI session ends in the middle of a task? I am collecting approaches, so tell me what works for you.

Voiceover: AI

#ClaudeCode #AIAgents #SoftwareEngineering #DeveloperProductivity #AIAutomation

==================== LINKEDIN FIRST COMMENT (copy this block) ====================

If your team uses Claude Code, Codex or any AI coding agent and keeps losing time to restarts, re-explaining and guessed decisions, I can help you set up:

- A parallel workflow so one developer can supervise several projects
- Context documents your agents actually follow
- Safe handoffs between sessions and providers, with secret scanning and spending caps

Contact: https://zahidul-islam.com/#contact

YouTube version with chapters: [LONG VIDEO LINK]


==================== YOUTUBE (long video) TITLE A (A/B test, pair with thumbnail-long-A.png) (copy this block) ====================

Claude Code + Codex: How I Run 4 Projects at the Same Time

==================== YOUTUBE (long video) TITLE B (A/B test, pair with thumbnail-long-B.png) (copy this block) ====================

Claude Code Usage Limit Hit? How I Keep Working Without Losing Context

==================== YOUTUBE (long video) TITLE C (A/B test, pair with thumbnail-long-C.png) (copy this block) ====================

Never Lose Context in Claude Code and Codex: switch-provider Skill

==================== YOUTUBE (long video) DESCRIPTION (copy this block) ====================

How to use Claude Code and Codex on 4 projects at the same time, and what to do when you hit a usage limit in the middle of a task. This is the exact AI coding workflow I use every day: four VS Code windows, four AI agents, six context documents and a skill I built called switch-provider. It hands your work to a new session or provider without losing what was decided, changed or tested.

AI coding agents changed the developer's job. The agent writes the code, runs it and tests it. You plan, review and decide. Once you are the reviewer instead of the typist, you are no longer limited to one project at a time. But two problems show up fast. Agents guess when they lack context, and every subscription has a usage limit. This video solves both.

CHAPTERS
0:00 One developer, four projects, four AI agents
0:21 The shift: from one line of work to parallel lanes
0:44 The setup: four VS Code windows with Claude Code and Codex
1:15 Context, not guesses: the six project documents
1:59 The real problem: usage limits in the middle of a task
2:22 The switch-provider skill, step by step
3:25 Subscription or OpenRouter: the human makes the call
3:51 How the new session picks up where the old one stopped
4:14 The whole system in three rules
4:33 Questions and contact

WHAT YOU WILL LEARN
- How to run several coding projects in parallel with Claude Code and Codex
- How to rotate between agents: plan, let it build, review, move to the next window
- The six context documents that stop AI agents from guessing
- Why the real cost of a usage limit is lost context, not lost time
- A safe, five-step handoff that works in both Claude Code and Codex
- How to continue on OpenRouter with a spending cap, without letting the agent spend money on its own

THE SIX CONTEXT DOCUMENTS
1. Requirements: what we are building and why
2. Architecture: the stack, the structure and the data flow
3. Design: colours, type and components
4. Memory: the current state and the next steps
5. Rules: commands and conventions the agent must follow (CLAUDE.md and AGENTS.md)
6. Tracker: every task, its status and its evidence

THE SWITCH-PROVIDER SKILL IN 5 STEPS
Run it with /switch-provider in Claude Code or $switch-provider in Codex.
1. Safe checkpoint: the agent finishes the smallest safe step. No half-written changes, and no commits just to switch.
2. Structured handoff: goal, constraints, decisions, changed files, tests that actually ran and their results, failures, remaining work, blockers and the next action. A test that did not run is never reported as passed.
3. Private memory: the checkpoint is saved to the project's memory folder after the helper confirms the folder is ignored by git. The current git state is recorded.
4. Secret scan: the checkpoint is scanned for keys and tokens and tied to the current launcher session. Anything sensitive gets it rejected until fixed.
5. Exit and choose: the agent says "Checkpoint saved. Type /exit." The launcher then offers Subscription (the default) or OpenRouter.

The agent never chooses the provider, spends credit, changes credentials or restarts processes. You do. The new session reads the checkpoint before doing anything else. It is a written handoff, not a replay of the old conversation.

A NOTE ON USAGE LIMITS
Claude Code subscription plans run on a rolling five-hour usage window plus a weekly cap, and Codex plans have their own limits. Check your plan's current numbers. They change. This workflow does not avoid limits. It makes sure a limit never costs you your progress.

ABOUT ME
I'm Zahidul Islam, an AI automation and full-stack engineer. I build AI-assisted development workflows, AI chatbots and automation for apps and websites.

Contact: https://zahidul-islam.com/#contact
Portfolio: https://zahidul-islam.com/
LinkedIn: https://www.linkedin.com/in/zahidul-islam-developer/
GitHub: https://github.com/Zahidulislam2222

What would you set up first: parallel windows, context documents or the provider switch? Tell me in the comments. I reply to every one.
Subscribe for more practical AI coding workflows.

Voiceover: AI

#ClaudeCode #Codex #AICoding

==================== YOUTUBE (long video) TAGS (copy this block) ====================

claude code, codex, claude code workflow, claude code usage limit, claude code limit reached, claude code vs codex, openai codex cli, ai coding agents, ai coding workflow, multiple projects at once, parallel ai agents, claude code openrouter, openrouter, claude code skills, claude code tips, vs code ai agent, context engineering, claude.md, agents.md, ai developer productivity, cluade code, claude-code, zahidul islam

==================== YOUTUBE (long video) PINNED COMMENT (copy this block) ====================

Quick question for the developers here.

When your AI coding agent hits its usage limit in the middle of a task, what do you do today?

1. Wait for the limit to reset
2. Open a new chat and explain everything again
3. Switch to another tool and hope it understands
4. I already have a handoff system (tell me how it works)

Reply with the number. I read and answer every comment.

If you want this workflow set up for your team or project, you can reach me here:
https://zahidul-islam.com/#contact


==================== YOUTUBE SHORTS (short video) TITLE (copy this block) ====================

Claude Code + Codex: 4 AI Agents, 1 Developer #shorts

==================== YOUTUBE SHORTS (short video) DESCRIPTION (copy this block) ====================

How one developer runs four projects at once with Claude Code and Codex, and keeps working when an agent hits its usage limit.

Full 5-minute breakdown: [LONG VIDEO LINK]

Each project has written context the agent reads first: requirements, architecture, design, memory, rules and a tracker. When a limit hits mid-task, my switch-provider skill writes a handoff with the goal, decisions, changed files, real test results and next steps. It saves the handoff privately and scans it for secrets, and then I choose Subscription or OpenRouter. The new session reads it and continues.

I'm Zahidul Islam, an AI automation and full-stack engineer.
https://zahidul-islam.com/

Voiceover: AI

#shorts #ClaudeCode #Codex #AICoding

==================== YOUTUBE SHORTS (short video) TAGS (copy this block) ====================

shorts, claude code, codex, claude code usage limit, ai coding agents, claude code workflow, parallel ai agents, openrouter, claude code tips, ai developer, vs code ai, coding with ai, cluade code, zahidul islam

==================== YOUTUBE SHORTS (short video) PINNED COMMENT (copy this block) ====================

How many AI coding agents do you run at the same time?

1. One
2. Two or three
3. Four or more

Reply with the number. The full workflow, with all five handoff steps, is in the long video: [LONG VIDEO LINK]


==================== FACEBOOK (long video) POST (copy this block) ====================

One developer. Four projects. All of them moving forward at the same time.

That is what my workday looks like now, and I want to show you exactly how it works, because I think most people are using AI coding tools the slow way.

I keep four VS Code windows open, one project in each. Two run Claude Code and two run Codex. I give the first one a clear task, and while it works I move to the second, then the third, then the fourth. When I come back to the first window, the work is done and waiting for me to review. The AI does the typing. I do the thinking and the checking.

There are two problems nobody warns you about.

The first one is guessing. If the AI does not know your decisions, it makes up its own. So every project has six short documents the AI reads before it starts: what we are building, how it is built, how it should look, where we are right now, the rules to follow, and a task list.

The second one is the usage limit. Every subscription has one, and it always seems to hit in the middle of a task. The worst part is not waiting. It is losing everything the AI knew: what was decided, what changed and what was already tested.

So I built a small tool called switch-provider. Before switching, it writes a clear handover note, checks it for passwords and keys, and saves it privately. Then it lets me choose: stay on my subscription, or continue on OpenRouter with a spending limit I set myself. The AI never decides that for me. The next session reads the note and carries on from the exact same spot.

The video explains the whole system in under five minutes, in simple words, with diagrams.

Do you use AI tools at work yet? Which one, and what annoys you most about it? Tell me in the comments. I read all of them.

Voiceover: AI

#ClaudeCode #AICoding #ArtificialIntelligence #Programming #Productivity

==================== FACEBOOK (long video) TAGS (copy this block) ====================

Claude Code, Codex, AI coding, AI agents, programming, software development, developer productivity, OpenRouter

==================== FACEBOOK (long video) FIRST COMMENT (copy this block) ====================

Want this kind of AI workflow for your team or your own project? I'm Zahidul Islam, an AI automation and full-stack engineer. I set up parallel AI coding workflows, context documents and safe handoffs, so your tools keep working without losing progress or guessing your decisions.

https://zahidul-islam.com/#contact


==================== INSTAGRAM + FACEBOOK (short video, Reel) CAPTION (copy this block) ====================

Claude Code and Codex: how one developer runs four projects at the same time.

Four VS Code windows. Four AI agents. I plan, they build, I review, and I move to the next window.

The part most people get wrong is what happens when an agent hits its usage limit halfway through a task. You do not just lose time. You lose everything it knew.

My fix is a skill called switch-provider:
1. It finishes a safe checkpoint, never half a change
2. It writes a handoff: goal, decisions, changed files, real test results, next steps
3. It saves the handoff privately and scans it for passwords and keys
4. I choose: my subscription or OpenRouter, with a spending cap I set
5. The new session reads the handoff and keeps going

The same skill works in Claude Code and Codex.

Save this for when you set up your own AI workflow, and send it to the developer friend who explains everything again every time a chat ends.

Full 5-minute breakdown: link in bio.

Voiceover: AI

#claudecode #aicoding #aiagents #softwaredeveloper #programming

==================== INSTAGRAM + FACEBOOK (short video, Reel) FIRST COMMENT (copy this block) ====================

Before you trust an AI agent to hand over a task, check five things:

1. Did it stop at a safe point, or in the middle of a change?
2. Did it write down what was decided?
3. Did it list only the tests that actually ran?
4. Did it remove every key and password?
5. Does a person choose what happens next?

Five yes answers and the next session can pick up safely. Which one does your setup miss? Tell me below.

https://zahidul-islam.com/

==================== INSTAGRAM + FACEBOOK (short video, Reel) EXTRAS (copy this block) ====================

Cover text (first frame or uploaded cover): 1 DEV. 4 AI AGENTS.
Facebook Reel tags: Claude Code, Codex, AI coding, AI agents, programming, developer
Instagram Alt text: Animated explainer showing four VS Code windows running Claude Code and Codex, and a five-step handoff when an AI agent hits its usage limit.
Location and topics: add the topic "Technology" when Instagram suggests topics.


==================== TIKTOK (short video) CAPTION (copy this block) ====================

How to use Claude Code and Codex on 4 projects at once, and what to do when you hit the usage limit mid-task.

I run four AI coding agents in parallel: two Claude Code, two Codex, one VS Code window per project. Each agent reads six context files first (requirements, architecture, design, memory, rules, tracker), so it follows my decisions instead of guessing.

When one hits its limit, my switch-provider skill:
1. Finishes a safe checkpoint
2. Writes a handoff with the goal, decisions, changed files, real test results and next steps
3. Saves it privately and scans it for secrets
4. Lets me pick my subscription or OpenRouter with a spending cap
5. The new session reads it and keeps going

No lost context and no explaining everything again. Full breakdown on my profile.

#claudecode #aicoding #codingtok #programming #softwareengineer

==================== TIKTOK (short video) FIRST COMMENT (copy this block) ====================

The question I get most: does the new session remember the old chat? No, and that is on purpose. It reads a written handoff with the goal, decisions, changed files, real test results and the next step. That is more reliable than a replayed conversation. Want this setup for your projects? Link in bio.

==================== TIKTOK (short video) EXTRAS (copy this block) ====================

On-screen hook text (first 2 seconds, TikTok searches on-screen text): 1 dev, 4 AI coding agents
Second text card (when the limit appears): what happens when Claude Code hits its limit?
Keywords to keep in caption, text and speech: claude code, codex, usage limit, ai coding agents, openrouter
Cover: thumbnail-short.png, or the frame with the four windows
Reply-with-video idea for comments: answer "how do I set up the context files?" with a 30-second follow-up showing the six documents.


==================== X (short video, upload natively) POST (copy this block) ====================

I run 4 coding projects at once: 2 with Claude Code, 2 with Codex.

The usage limit is not the real problem. Losing context mid-task is.

So my agents write a handoff, scan it for secrets, and I pick the next provider. The agent never decides alone.

==================== X FIRST REPLY (copy this block) ====================

Full 5-minute breakdown with the six context files and all five handoff steps: [LONG VIDEO LINK]

More of my work: https://zahidul-islam.com/

==================== X THREAD (optional, post later as a separate post) (copy this block) ====================

1/ Most AI coding mistakes are not bad code. They are guesses. Here is how I stop my agents from guessing across 4 projects at once.

2/ Every project has six files the agent reads first: requirements, architecture, design, memory, rules, tracker. A decision is written once and followed every time.

3/ When a usage limit hits mid-task, the agent finishes a safe checkpoint and writes a handoff: goal, decisions, changed files, tests that actually ran, blockers, next action.

4/ A helper saves it to private memory and scans it for keys and tokens. If something sensitive is found, the handoff is rejected until it is fixed.

5/ Then I choose: subscription or OpenRouter with a spending cap. The new session reads the handoff and continues. Not a replayed chat, a written handover.


==================== POSTING ORDER AND TIMING NOTES ====================

1. YouTube long video first, with all three thumbnails in Test and compare. Use the title that matches each thumbnail.
2. YouTube Short the same day, with the long video added as the related video.
3. LinkedIn: upload the long MP4 natively the next working morning. Post the first comment right away and reply to every comment in the first hour.
4. Instagram Reel, shared to Facebook as a Reel, with the Facebook Reel tags added.
5. TikTok the same day as the Reel, with a different caption (above). Pin the first comment.
6. Facebook long video one or two days later, so it does not compete with the Reel.
7. X: upload the short MP4 natively and put the link in the first reply. Post the thread a few days later if the first post gets replies.

SOURCES USED FOR THE PLATFORM RESEARCH
- YouTube limits: https://influencermarketinghub.com/youtube-character-limits/ and https://howmanywords.app/blog/youtube-character-limits
- YouTube SEO: https://www.vidiq.com/blog/post/youtube-seo/
- Shorts SEO: https://miraflow.ai/blog/youtube-shorts-seo-2026-how-to-rank-in-search and https://metadatareactor.com/blog/youtube-shorts-seo-guide/
- LinkedIn: https://www.visla.us/blog/guides/linkedin-video-in-2026-whats-working-and-how-to-make-it/ and https://www.webtures.com/insights/linkedin-algorithm-2026/
- Instagram 5-hashtag limit: https://www.socialmediatoday.com/news/instagram-implements-new-limits-on-hashtag-use/808309/
- Instagram captions and search: https://lamplightcreatives.com/captions-vs-hashtags-instagram-2026/ and https://later.com/blog/instagram-reels-algorithm/
- Cross-posting Reels: https://posteverywhere.ai/blog/how-to-cross-post-instagram-reels-to-facebook-reels
- Facebook: https://www.socialpilot.co/blog/facebook-engagement-tips and https://animoto.com/blog/video-marketing/facebook-video-search-optimization
- TikTok: https://metricool.com/tiktok-seo/, https://ttcalculator.net/guides/growth/tiktok-seo-search-ranking/ and https://www.bulkpublish.com/blog/tiktok-character-limit/
- X: https://socialpilot.co/blog/twitter-algorithm and https://posteverywhere.ai/blog/how-the-x-twitter-algorithm-works
- Claude Code limits: https://support.claude.com/en/articles/15910845-claude-code-may-july-2026-weekly-limits-promotion
Most of these are practitioner and vendor guides, not official platform documentation, and they disagree on some numbers. The Instagram 5-hashtag limit and the X 280-character limit are the most firmly established points.
