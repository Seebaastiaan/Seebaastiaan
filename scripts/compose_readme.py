"""Compose the full cream-and-black README image; Python 3.10+, stdlib only."""
from pathlib import Path
from html import escape
import re
import textwrap

ROOT=Path(__file__).resolve().parents[1]
parts=[]
y=0

def text(value, x=64, size=25, font='Georgia, Times New Roman, serif', color='#111110', weight='normal', italic=False):
    global y
    style=' font-style="italic"' if italic else ''
    parts.append(f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" font-weight="{weight}" fill="{color}"{style}>{escape(value)}</text>')

def paragraph(value, width=86, size=25, leading=37):
    global y
    for line in textwrap.wrap(value,width=width):
        text(line,size=size)
        y+=leading

def section(label):
    global y
    y+=20
    parts.append(f'<path d="M64 {y}H1136" stroke="#d1cbbf"/>')
    y+=52
    text('— '+label,size=17,font='Courier New, monospace',color='#565146')
    y+=48

header=(ROOT/'assets/editorial-header.svg').read_text()
header=re.sub(r'<svg\b', '<svg x="0" y="0"', header, count=1)
parts.append(header)
y=340
text('I build web experiences and explore how intelligence takes shape.',size=27,italic=True)
y+=43
text('Thoughtful interfaces. Curious engineering.',size=21,font='Courier New, monospace',color='#565146')
y+=16
section('CURRENTLY')
paragraph('Studying Artificial Intelligence Engineering at ESCOM, Instituto Politécnico Nacional (IPN).')
y+=14
paragraph('Building a neurodynamic engine to explore neural activity and stimulus propagation through simulated networks, while learning how to build AI from the ground up.')
section('ELSEWHERE')
text('portfolio-sebas-jara24.vercel.app',size=25);y+=38
text('linkedin.com/in/sebastianjara24',size=25);y+=38
text('sebasjara1503@gmail.com',size=25);y+=18
section('WORK')
projects=[
('01 / LearnQuest','Gamified entrance exam preparation, with subject-based practice, XP, and progress tracking.','Next.js · TypeScript · Supabase'),
('02 / MindfulSpace','A digital journal with an AI companion and mood tracking for personal reflection.','Next.js · TypeScript · Firebase · Gemini API'),
('03 / Algoritmo Lanczos','Eigenvalue and eigenvector approximation for symmetric matrices, implemented in C.','C · Linear algebra · Numerical methods'),
('04 / RailSense','Interactive railway analytics powered by AI. I developed the entire user interface.','Next.js · TypeScript · Tailwind CSS · Recharts')]
for title,description,stack in projects:
    text(title,size=33,weight='bold');y+=42
    paragraph(description)
    text(stack,size=20,font='Courier New, monospace',color='#565146');y+=65
section('ABOUT, IN CODE')
code=[
'profile = {',
'    "role": "AI Engineer",',
'    "education": "AI Engineering · ESCOM / IPN",',
'    "interests": ["Interface design", "Web applications", "AI"],',
'    "building": "A neurodynamic engine",',
'    "learning": "How to build AI from the ground up",',
'    "open_to": ["Job opportunities", "Project collaborations"],',
'}']
for line in code:
    text(line,size=22,font='Courier New, monospace');y+=34
y+=4
section('TOOLKIT')
text('LANGUAGES',size=16,font='Courier New, monospace',color='#565146');y+=37
text('TypeScript · JavaScript · Python · C · SQL',size=25);y+=49
text('WEB & PLATFORMS',size=16,font='Courier New, monospace',color='#565146');y+=37
text('React · Next.js · Tailwind CSS · Supabase · Firebase · Git',size=25);y+=18
section('RECOGNITION')
text('Open Source Winner',size=33,weight='bold');y+=41
text('Hackathon Mobility & AI · November 2025',size=25);y+=39
paragraph('RailSense — Developed the entire user interface.')
y+=28
text('3rd Place · Software Development',size=33,weight='bold');y+=41
paragraph('Premio a los mejores Prototipos de Nivel Medio Superior, IPN')
text('June 2024 · Uxersii · Full stack developer',size=25);y+=18
section('CONTRIBUTION SKYLINE')
# Embed the generated calendar with a distinct accessibility id namespace.
skyline=(ROOT/'assets/contribution-skyline.svg').read_text()
skyline=skyline.replace('id="title"','id="skyline-title"').replace('id="desc"','id="skyline-desc"').replace('aria-labelledby="title desc"','aria-labelledby="skyline-title skyline-desc"')
skyline=re.sub(r'<svg\b[^>]*>',f'<svg x="40" y="{y-20}" width="1120" height="448" viewBox="0 0 1200 480" role="img" aria-labelledby="skyline-title skyline-desc">',skyline,count=1)
parts.append(skyline);y+=470
paragraph('One block is one day. Height represents contributions from my public GitHub calendar, including activity beyond commits.',size=22,leading=32,width=92)
y+=5
section("LET'S BUILD")
paragraph("I'm looking for job opportunities and people to build projects with, especially around interfaces, web applications, and AI.")
y+=27
parts.append(f'<path d="M64 {y}H1136" stroke="#d1cbbf"/>');y+=41
text('issue №01 · 2026 · written in this README',size=16,font='Courier New, monospace',color='#565146');y+=45
svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{y}" viewBox="0 0 1200 {y}" role="img" aria-labelledby="readme-title readme-desc"><title id="readme-title">Sebastian Jara — AI Engineer</title><desc id="readme-desc">Full profile: AI Engineering student at ESCOM IPN. Building a neurodynamic engine. Selected work: LearnQuest, MindfulSpace, Algoritmo Lanczos, RailSense. Open Source Winner at Hackathon Mobility and AI, November 2025. Third Place Software Development at IPN, June 2024, Uxersii. Open to work and project collaborations. Project and contact links follow this image.</desc><rect width="1200" height="{y}" fill="#f2f0e9"/>'+''.join(parts)+'</svg>'
(ROOT/'assets/readme-cream.svg').write_text(svg)
icons = {
    'linkedin': '<rect x="22" y="16" width="17" height="17" rx="1.5" fill="#111110"/><circle cx="26" cy="20" r="1.2" fill="#f2f0e9"/><path d="M26 23v7M30 30v-7m0 3c0-4 5-4 5 0v4" fill="none" stroke="#f2f0e9" stroke-width="1.8"/>',
    'email': '<rect x="21" y="17" width="20" height="15" rx="1.5" fill="none" stroke="#111110" stroke-width="1.6"/><path d="m22 18 9 7 9-7" fill="none" stroke="#111110" stroke-width="1.6"/>',
    'twitter': '<path d="M22 16h4.2L40 33h-4.2ZM38 16h2L24 33h-2Z" fill="#111110"/>',
}
buttons=[('portfolio','PORTFOLIO'),('linkedin','LINKEDIN'),('email','EMAIL'),('twitter','TWITTER'),('learnquest','LEARNQUEST'),('mindfulspace','MINDFULSPACE'),('lanczos','LANCZOS'),('railsense','RAILSENSE')]
for filename,label in buttons:
    icon=icons.get(filename, '')
    width=max(150,len(label)*13+46+(28 if icon else 0))
    text_attributes='x="52"' if icon else f'x="{width/2}" text-anchor="middle"'
    (ROOT/f'assets/link-{filename}.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="48" viewBox="0 0 {width} 48" role="img" aria-label="{label}"><rect width="{width}" height="48" fill="#f2f0e9"/>{icon}<text {text_attributes} y="30" font-family="Courier New, monospace" font-size="17" fill="#111110">{label} ↗</text></svg>')
print(f'Composed full README: 1200 × {y}')
