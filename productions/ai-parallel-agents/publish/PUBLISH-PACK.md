# Publish pack: Parallel AI agents and the switch-provider skill

Files:
- Long video: `long-landscape.mp4` (1920x1080, 4:43)
- Short video: `short-portrait.mp4` (1080x1920, 1:17)
- Thumbnails: `thumbnail-long-A.png`, `thumbnail-long-B.png`, `thumbnail-long-C.png` (1280x720) and `thumbnail-short.png` (1080x1920)

Ground rules used for every platform:
- The search keyword comes in the first line, because most platforms index captions and only show the first line or two before "more".
- Each platform gets its own hook and its own call to action. Nothing is copied word for word between platforms.
- No emojis. No invented numbers. Every claim matches what the video shows.
- Links go where each platform punishes them least. That is in the reply on X, in the first comment on LinkedIn and Facebook, and in the bio on Instagram and TikTok.
- AI voice disclosure ("Voiceover: AI") is kept on every platform. On YouTube, also tick the altered or synthetic content setting if the upload screen asks.

Fill in before posting:
- [LONG VIDEO LINK]: the YouTube URL of the long video, once it is live.


==================== YOUTUBE (long video) TITLE A (pair with thumbnail-long-A.png) ====================

How I Run 4 Projects at Once with Claude Code and Codex

==================== YOUTUBE (long video) TITLE B (pair with thumbnail-long-B.png) ====================

Claude Code Usage Limit Hit? Switch Providers Without Losing Work

==================== YOUTUBE (long video) TITLE C (pair with thumbnail-long-C.png) ====================

My switch-provider Skill: Claude Code, Codex and OpenRouter Handoff

==================== YOUTUBE (long video) DESCRIPTION ====================

How do you run four coding projects at the same time with Claude Code and Codex, and keep going when one of them hits its usage limit in the middle of a task? This video shows the exact workflow I use every day. Four VS Code windows, four AI agents, and a skill I built called switch-provider. It hands the task over to a new session without losing what was decided, changed or tested.

AI coding agents changed the job. The agent writes, runs and tests the code. You plan, review and decide. Once you are the reviewer and not the typist, one project at a time stops being the limit.

CHAPTERS
0:00 One developer, four projects, four AI agents
0:21 The shift: from one line of work to parallel lanes
0:44 The setup: four VS Code windows, Claude Code and Codex
1:15 Context, not guesses: the six project documents
1:59 The real problem: usage limits in the middle of a task
2:22 The switch-provider skill, step by step
3:25 Subscription or OpenRouter: you make the call
3:51 How the new session picks up where the old one stopped
4:14 The whole system in three rules
4:33 Questions and contact

THE SETUP
Each project gets its own VS Code window and its own agent in the terminal. Two windows run Claude Code and two run Codex. I give window one a clear task, move to window two while it works, then three, then four. By the time I am back at window one, there is finished work waiting for review.

THE SIX CONTEXT DOCUMENTS
Most AI coding mistakes come from guessing, not from bad code. So every project carries six documents the agent reads before it starts:
1. Requirements: what we are building and why
2. Architecture: the stack, the structure and the data flow
3. Design: colours, type and components
4. Memory: the current state and the next steps
5. Rules: the commands and conventions to follow (CLAUDE.md and AGENTS.md)
6. Tracker: every task, its status and its evidence

WHAT SWITCH-PROVIDER DOES
Claude Code plans run on a rolling five-hour usage window plus a weekly cap. Codex plans have their own limits. When one of them runs out mid-task, the work is fine. The context is what gets lost. switch-provider protects it in five steps:
1. The agent finishes the smallest safe checkpoint. No half-written changes, and no commits just to switch.
2. It writes a structured handoff: goal, constraints, decisions, changed files, the tests that actually ran and their results, failures, remaining work, blockers and the next action. A test that did not run is never reported as passed.
3. A helper saves the checkpoint into the project's private memory folder. It first checks that the folder is ignored by git, then records the git state.
4. A second helper scans the checkpoint for secrets such as keys and tokens and ties it to the current launcher session. If anything sensitive is found, the handoff is rejected until it is fixed.
5. The agent says "Checkpoint saved. Type /exit." The launcher then offers two options: Subscription (the default) or OpenRouter.

You run it with /switch-provider in Claude Code or $switch-provider in Codex. The agent never picks the provider, spends credit, changes credentials or restarts anything by itself. OpenRouter is pay as you go, through an API key with a spending cap I set myself.

The new session is not a replay of the old conversation. It reads a clean, written handoff, which is why it can continue with the goal, what is done, what is verified and what comes next.

ABOUT ME
I'm Zahidul Islam, an AI automation and full-stack engineer. I build AI-assisted development workflows, AI chatbots and automation for apps and websites.

Contact: https://zahidul-islam.com/#contact
Portfolio: https://zahidul-islam.com/
LinkedIn: https://www.linkedin.com/in/zahidul-islam-developer/
GitHub: https://github.com/Zahidulislam2222

Which part of this workflow would you set up first: the parallel windows, the context documents or the provider switch? Tell me in the comments.

Voiceover: AI

#ClaudeCode #Codex #AICoding

==================== YOUTUBE (long video) TAGS ====================

claude code, codex, openai codex, claude code workflow, claude code usage limit, claude code rate limit, ai coding agents, ai coding workflow, multiple projects at once, parallel ai agents, vs code ai agent, openrouter, openrouter claude code, claude code skills, switch provider, ai developer productivity, context engineering, claude.md, agents.md, cluade code, zahidul islam

==================== YOUTUBE (long video) PINNED COMMENT ====================

Honest question for the developers here.

When your AI coding agent hits its limit in the middle of a task, what do you do right now?

1. Wait for the limit to reset
2. Start a new chat and explain everything again
3. Switch to another tool and hope it figures it out
4. Something smarter (tell me what)

Reply with the number. I read and answer every comment.

If you want this kind of setup in your own team or project, here is where to reach me:
https://zahidul-islam.com/#contact


==================== YOUTUBE SHORTS (short video) TITLE ====================

1 Developer, 4 AI Coding Agents: Claude Code and Codex Workflow #shorts

==================== YOUTUBE SHORTS (short video) DESCRIPTION ====================

One developer, four projects and four AI coding agents running at the same time. Two windows run Claude Code and two run Codex.

The full 5-minute breakdown is here: [LONG VIDEO LINK]

How it works:
Every project has written context the agent reads first: requirements, architecture, design, memory, rules and a tracker. That way it follows decisions instead of guessing.

When one agent hits its usage limit mid-task, my switch-provider skill finishes a safe checkpoint and writes a handoff: goal, decisions, changed files, real test results and next steps. It saves the handoff to private project memory and scans it for secrets. After that, the launcher asks: Subscription or OpenRouter, with a spending cap I set. The new session reads the handoff and the work continues.

The same skill works in Claude Code and Codex.

I'm Zahidul Islam, an AI automation and full-stack engineer.
https://zahidul-islam.com/

Voiceover: AI

#shorts #ClaudeCode #AICoding

==================== YOUTUBE SHORTS (short video) TAGS ====================

shorts, claude code, codex, ai coding agents, claude code workflow, claude code usage limit, openrouter, parallel ai agents, ai developer, coding with ai, vs code ai, developer productivity, zahidul islam

==================== YOUTUBE SHORTS (short video) PINNED COMMENT ====================

How many AI agents do you run at the same time?

1. Just one
2. Two or three
3. Four or more

Reply with the number. The full workflow, including the provider switch, is in the long video on my channel.


==================== LINKEDIN POST (upload the long video natively, not as a YouTube link) ====================

I run four projects at the same time. The hard part was never the code.

It was the moment an AI agent hits its usage limit halfway through a task.

The limit itself is not the real cost. Losing the context is: what was decided, what changed, what was tested and what is left. Lose that, and the next session starts from zero.

Here is the setup I use every day.

Four VS Code windows, one project in each. Two run Claude Code and two run Codex. I give each one a clear task and rotate: plan, review, next window. The agents build. I keep the direction.

Two things keep the error rate low.

First, written context. Every project carries six documents the agent reads before it starts: requirements, architecture, design, memory, rules and a task tracker. Most AI mistakes come from guessing. Written decisions remove the guessing.

Second, a clean handoff. When a limit hits, I run a skill I built called switch-provider. It:
1. Finishes the smallest safe checkpoint, with no half-written changes
2. Writes a structured handoff: goal, decisions, changed files, the tests that actually ran, failures, blockers and the next action
3. Saves it to private project memory and records the git state
4. Scans it for secrets and rejects it if anything sensitive shows up
5. Hands control back to me to choose Subscription or OpenRouter, with a spending cap I set

The agent never chooses the provider or spends money on its own. That decision stays with a person.

What surprised me most: the handoff document became the best documentation in each project. It is written for an agent with no memory, so it is clear enough for any developer joining later.

Speed in this era is not about typing faster. It is about using these tools properly.

The full 5-minute breakdown is in the video above.

How do you handle context when an AI session ends in the middle of a task? I would like to compare approaches in the comments.

Voiceover: AI

#ClaudeCode #AICoding #SoftwareEngineering #DeveloperProductivity #Automation

==================== LINKEDIN FIRST COMMENT ====================

If you want this setup in your team (parallel agents, context documents and safe handoffs between providers), I help companies and developers build AI-assisted workflows that hold up in real projects.

https://zahidul-islam.com/#contact

The YouTube version, with chapters: [LONG VIDEO LINK]


==================== FACEBOOK (long video) POST ====================

Four projects. One developer. All moving at the same time.

This is what software work looks like now. AI coding agents write, run and test the code, and I review and steer. Two of my windows run Claude Code and two run Codex.

But there is a problem nobody talks about. Every subscription has a usage limit. When an agent runs out halfway through a task, you lose more than time. You lose the context: what was decided, what changed and what was tested.

So I built a small skill called switch-provider. Before switching, it saves a clean handoff note, checks it for passwords and keys, and then lets me choose: keep my subscription, or continue on OpenRouter with a spending limit I set myself. The new session reads the note and carries on from the exact same spot.

The video explains the whole system in under five minutes, in plain words, with diagrams.

Do you use AI tools in your work yet? Which one, and what is the most annoying part? Tell me below.

Voiceover: AI

#ClaudeCode #AICoding #Productivity

==================== FACEBOOK (long video) FIRST COMMENT ====================

Want this kind of AI workflow set up for your team or your project? I'm Zahidul Islam, an AI automation and full-stack engineer.

https://zahidul-islam.com/#contact

==================== FACEBOOK REEL (short video) CAPTION ====================

1 developer, 4 AI coding agents, and a plan for when one of them runs out of usage. Two Claude Code windows, two Codex windows, and a handoff skill that saves the context before switching. Would you work this way? Yes or no.

Voiceover: AI

#ClaudeCode #AICoding #Developer


==================== INSTAGRAM REEL (short video) CAPTION ====================

AI coding workflow: one developer running four projects with Claude Code and Codex at the same time.

Here is how it works:
1. Four VS Code windows, one project and one AI agent each
2. Every project has six documents the agent reads first, so it follows decisions instead of guessing
3. When an agent hits its usage limit mid-task, the switch-provider skill writes a handoff: goal, decisions, changed files, real test results and next steps
4. The handoff is saved privately and scanned for secrets
5. I choose to continue on my subscription or on OpenRouter, with a spending cap I set
6. The new session reads the handoff and keeps going

Save this for when you set up your own AI workflow. Send it to the developer friend who still loses context every time a chat ends.

The full 5-minute version is linked in my bio.

Voiceover: AI

#claudecode #aicoding #developer #codinglife #softwareengineer

==================== INSTAGRAM REEL FIRST COMMENT ====================

Before you trust an AI agent with a handoff, check these five things:

1. Did it finish a safe step, or stop halfway?
2. Did it write down what was decided?
3. Did it list the tests that actually ran?
4. Did it remove keys and passwords?
5. Does a person choose what happens next?

Five yes answers mean the next session can pick up safely. More on my website, link in bio.


==================== TIKTOK (short video) CAPTION ====================

How to use Claude Code and Codex on four projects at once without losing work when you hit a usage limit. I run four AI coding agents in parallel, and when one runs out mid-task, my switch-provider skill writes a handoff note, scans it for secrets and lets me continue on my subscription or OpenRouter. The new session reads the note and keeps going. Full breakdown on my profile.

#claudecode #aicoding #codingtok #programming #developer

On-screen text for the first 2 seconds (TikTok also searches on-screen text): "1 dev, 4 AI coding agents"

==================== TIKTOK FIRST COMMENT ====================

The question I get most: does the new session remember everything? No. It reads a written handoff with the goal, decisions, changed files, real test results and next step. That is more reliable than a replayed chat. Want this setup? Link in bio.


==================== X (short video, upload natively) POST ====================

I run 4 coding projects at once: 2 with Claude Code, 2 with Codex.

The real problem is not the usage limit. It is losing context when the limit hits mid-task.

My fix: a skill that writes a handoff, scans it for secrets and lets me pick the next provider. The agent never decides on its own.

==================== X FIRST REPLY ====================

Full 5-minute breakdown with the six context documents and all five handoff steps: [LONG VIDEO LINK]

More of my work: https://zahidul-islam.com/

==================== X THREAD (optional, post after the video gets replies) ====================

1/ Most AI coding mistakes are not bad code. They are guesses. Here is how I stop my agents from guessing across 4 projects at once.

2/ Every project has six documents the agent reads before it starts: requirements, architecture, design, memory, rules, tracker. Decisions are written once and followed every time.

3/ When a usage limit hits mid-task, the agent finishes a safe checkpoint and writes a handoff: goal, decisions, changed files, tests that actually ran, blockers, next action.

4/ A helper saves it to private memory and scans it for keys and tokens. If something sensitive is found, the handoff is rejected until it is fixed.

5/ Then I choose: subscription or OpenRouter with a spending cap. The new session reads the handoff and continues. Not a replayed chat, a written handover.


==================== POSTING NOTES ====================

- YouTube: upload all three long thumbnails in Test and compare, and keep the title that fits each one (A, B or C). Add the chapters exactly as written so they show in the player and in Google.
- YouTube Shorts: set thumbnail-short.png as the cover where the app allows. The key text sits in the centre so it survives the grid crop.
- LinkedIn and X: upload the video file natively. A pasted YouTube link gets less reach on both.
- Instagram, TikTok and Facebook Reels: use the short video. The long video goes on Facebook as a normal video post.
- Reply to early comments within the first hour on every platform. Comments and replies weigh more than likes everywhere.
