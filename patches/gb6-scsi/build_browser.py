
from pathlib import Path
import sys,struct,hashlib,json,pypcode
from build_config import ROOT as R, OUTPUT as P, OS_SOURCE, SOURCE
sys.path.insert(0,str(SOURCE))
from asmkit import Asm
C=0x5fc0;B=0x5bf0;RESOURCE=0x5cd0;RESOURCE_UI=0x9cd0
MENU=C+92
LCD=0x5a50;LCD_UI=0x9a50;TMP=0x5b30;SCROLL=C+40
EXTRA=0x5900
extra=bytearray();extra_strings={}
for key,value in [("collections","Image Library - Collections"),("disk","Image Library - Disk options"),("id1","Image Library - ISO A (ID 1)"),("id2","Image Library - IMG (ID 2)"),("id3","Image Library - ISO B (ID 3)"),("id6","Image Library - ISO C (ID 6)"),("help0","Select collection   Exit: close"),("help1","Select image: mount + Load   Exit: close"),("help2","Select disk operation   Exit: close"),("confirm","Confirm image"),("mount","Mount + Load"),("back","Back")]:
 extra_strings[key]=EXTRA+len(extra);extra.extend(value.encode()+b"\0")
assert len(extra)<=0x150
MODE=C+32;TARGET=C+34;COUNT=C+36;FIRST=C+38;CDB=C+56;ERROR=C+44
original=OS_SOURCE.read_bytes();assert hashlib.sha256(original).hexdigest()=='3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd'
# Native descriptor/geometry, with owned labels, fields, tuples and callbacks.
blob=bytearray(32);blob[16:32]=bytes.fromhex('0100032814f0c000f40000009600c400')
labels=len(blob);blob.extend(bytes([1,0,0x80])+b'Image Library'+b'\0');text=[]
for row in range(9):
 blob.extend(bytes([1,2+row*2,0xf0]));text.append(RESOURCE+len(blob));blob.extend(b' '*32+b'\0')
blob.extend(b'\xff');fieldptr=len(blob);blob.extend(b'\0\0');tupleptr=len(blob);blob.extend(b'\0\0');fieldlist=len(blob)
for row in range(9):blob.extend(bytes([0,2+row*2,40,2,0,row,4]))
blob.extend(b'\xff\xff\0');tuples=len(blob);blob.extend(bytes(9*4)+b'\xff\xff');callbacks=len(blob);blob.extend(bytes(40));blank=len(blob);blob.extend(b'\0')
struct.pack_into('<8H',blob,0,RESOURCE_UI+labels+3,RESOURCE_UI+16,RESOURCE_UI+labels,RESOURCE_UI+fieldptr,RESOURCE_UI+fieldptr,RESOURCE_UI+fieldptr,RESOURCE_UI+tupleptr,RESOURCE_UI+callbacks)
struct.pack_into('<H',blob,fieldptr,RESOURCE_UI+fieldlist);struct.pack_into('<H',blob,tupleptr,RESOURCE_UI+tuples)
for row,t in enumerate(['ISO A (ID 1)','IMG (ID 2)','ISO B (ID 3)','ISO C (ID 6)']):off=text[row]-RESOURCE;blob[off:off+len(t)]=t.encode()
signature=639
message_cancel=683;message_uncertain=693;message_error=723;message_busy=734
assert len(blob)<0x3f0
saved=list(range(0x1c,0x60,2))+[0xda]
a=Asm()
ALL_SAVED=tuple(saved);callback_bodies=[]
def prologue():
 n=len(callback_bodies);callback_bodies.append(n)
 a.emit(0xf4,0xc8,0x1e);a.label(f'entry_literal_{n}');a.imm(0x1e,0);a.jmp('common_prologue');a.label(f'body_{n}')
def epilogue():a.emit(0xf0)

def plus(r,n):a.emit(0x65,n&255,n>>8,r)
def native(target,page):a.imm(0x1c,page);a.imm(0x1e,target);a.call('cded');a.imm(0x1c,15);a.st(0x1c,0x10a)
def rowptr():
 a.emit(0x09,5,0x44);plus(0x44,B)
def highlight():
 a.ldb(0x44,0x2476);a.cmpb(0x44,0);name='skip_highlight_'+str(len(a.code));a.cond(0xdf,name);native(0x9460,0x196);a.label(name)

def repaint():
 a.stb(0,0x2152);a.stb(0,RESOURCE+26);a.call('clear_draw');highlight()
a.label('action');prologue();a.stb(0,C+31);a.st(0,C+16);a.st(0,ERROR);a.st(0,C+86);a.byte(0x44,1);a.stb(0x44,C+18);a.call('admit');a.cond(0xd7,'admission_busy');a.call('quiet_enter');a.cond(0xdb,'admission_busy');a.call('admit');a.cond(0xd7,'admission_busy');a.mov(0x4e,0xb6);a.emit(0x08,8,0x4e);a.ldb(0x44,0x2476);a.cmpb(0x44,0);a.cond(0xd7,'action_index_ready');a.ld(0x44,SCROLL);a.emit(0x64,0x44,0x4e);a.emit(0xb0,0x4e,0xb7);a.label('action_index_ready')
# Removed unused native-field diagnostic snapshots to fund admission.
a.ld(0x44,MODE);a.cmp(0x44,3);a.cond(0xdf,'confirm_action');a.cmp(0x44,2);a.cond(0xdf,'native_action');a.cmp(0x44,0);a.cond(0xd7,'image_action')
a.cmp(0x4e,5);a.cond(0xdf,'disk_operations');a.cmp(0x4e,3);a.cond(0xd9,'action_end')
a.imm(0x48,RESOURCE+blank+1);a.emit(0x64,0x4e,0x48,0xb2,0x48,0x44);a.st(0x44,TARGET)
a.imm(0x44,1);a.st(0x44,MODE);a.st(0,FIRST);a.call('discover');a.cmp(0x3e,0);a.cond(0xd7,'catalog_error');a.label('reload_page');a.call('get_catalog');a.cmp(0x3e,0);a.cond(0xd7,'catalog_error');a.call('admit');a.cond(0xd7,'admission_busy');a.jmp('render_repaint')
a.label('disk_operations');a.imm(0x44,2);a.st(0x44,MODE);a.jmp('render_repaint')
a.label('native_action');a.call('quiet_leave');a.call('admit');a.cond(0xd7,'admission_busy');a.st(0,MODE);a.imm(0x44,1);a.st(0x44,C+90);a.ldb(0x44,0x2476);a.cmpb(0x44,0);a.cond(0xdf,'lcd_native_action');native(0x94d9,0x196);a.jmp('action_end');a.label('lcd_native_action');native(0x9798,0x196);a.jmp('action_end')
a.label('image_action');a.cmp(0x4e,7);a.cond(0xdf,'previous');a.cmp(0x4e,8);a.cond(0xdf,'next')
a.ld(0x44,FIRST);a.emit(0x64,0x4e,0x44);a.ld(0x46,COUNT);a.emit(0x88,0x46,0x44);a.cond(0xdb,'action_end');a.stb(0x44,C+42)
a.ldb(0x44,0x2476);a.cmpb(0x44,0);a.cond(0xd7,'mount_selected');a.imm(0x44,3);a.st(0x44,MODE);a.call('render');repaint();a.imm(0xd0,24);a.byte(0xd2,8);a.jmp('action_end')
a.label('confirm_action');a.cmp(0x4e,2);a.cond(0xdf,'mount_selected');a.cmp(0x4e,3);a.cond(0xd7,'action_end');a.imm(0x44,1);a.st(0x44,MODE);a.jmp('render_repaint')
a.label('mount_selected');a.call('mount');a.cmp(0x3e,0);a.cond(0xd7,'catalog_error');a.call('admit');a.cond(0xd7,'admission_busy');a.call('quiet_leave');a.call('admit');a.cond(0xd7,'admission_busy');a.imm(0x44,0x7601);a.st(0x44,C+84)
a.st(0,MODE);a.st(0,FIRST);a.call('render')
# Guest updates the ordinary native selected-drive parameter, then queues Disk Load.
a.emit(0xcb,1,0x0c,1);a.imm(0x1c,0x299);a.st(0x1c,0x10c);a.ld(0x44,TARGET);a.stb(0x44,0x8f7d);a.emit(0xcf,1,0x0c,1)
a.imm(0x44,1);a.st(0x44,C+90);a.byte(0x48,2);a.call('event');a.imm(0x4a,0xf6);a.ldb(0x44,0x2476);a.cmpb(0x44,0);a.cond(0xd7,'load_screen_ready');plus(0x4a,1);a.label('load_screen_ready');a.call('screen');a.jmp('action_end')
a.label('previous');a.ld(0x44,FIRST);a.cmp(0x44,0);a.cond(0xdf,'collections');a.emit(0x69,7,0,0x44);a.st(0x44,FIRST);a.jmp('reload_page')
a.label('next');a.ld(0x44,FIRST);plus(0x44,7);a.ld(0x46,COUNT);a.emit(0x88,0x46,0x44);a.cond(0xdb,'action_end');a.st(0x44,FIRST);a.jmp('reload_page')
a.label('catalog_error');a.st(0x3e,ERROR);a.label('collections');a.st(0,MODE)
a.label('render_repaint');a.call('render');repaint()
a.jmp('action_end');a.label('admission_busy');a.imm(0x44,11);a.st(0x44,ERROR);a.jmp('collections');a.label('action_end');a.call('quiet_leave');a.stb(0,C+18);epilogue()
# Match native disk busy policy during an action, retaining idle-browser MIDI.
# C+30 holds the original native controller mode; C+31 is a scoped lease flag.
a.label('quiet_enter');a.clr(0x44);a.ldb(0x44,0x1ba5);a.st(0x44,C+30);a.byte(0x4a,0);a.call('controller_mode');a.cond(0xdb,'quiet_return');a.byte(0x44,1);a.stb(0x44,C+31);a.emit(0xf8);a.label('quiet_return');a.emit(0xf0)
a.label('quiet_leave');a.ldb(0x44,C+31);a.cmpb(0x44,0);a.cond(0xdf,'quiet_leave_return');a.stb(0,C+31);a.ldb(0x4a,C+30);a.call('controller_mode');a.label('quiet_leave_return');a.emit(0xf0)
# Native001F:4F8D is the controller transition without4F7F's UI redraw.
# Native shutdown waits for its timer ISR, so call only with the original
# caller's interrupt permission and masks. No unconditional EI for masked callers.
a.label('controller_mode');a.ld(0x44,C+8);a.emit(0x39,0x45,3);a.jmp('controller_masked');a.emit(0x3d,0x44,3);a.jmp('controller_masked');a.emit(0xc8,0xb6);a.ld(0x46,C+10);a.ld(0x48,C+6);a.st(0x48,0x10a);a.emit(0xb0,0x4a,0x9d,0xb0,0x44,8,0xb0,0x47,0x13,0xfb);a.imm(0x1c,31);a.imm(0x1e,0x4f8d);a.call('ce14');a.emit(0xfa);a.byte(8,0);a.byte(0x13,0);a.imm(0x1c,15);a.st(0x1c,0x10a);a.emit(0xcc,0xb6,0xf8,0xf0);a.label('controller_masked');a.emit(0xf9,0xf0)

a.label('admit');a.ldb(0x44,0x2bba);a.cmpb(0x44,0);a.cond(0xd7,'admit_return');a.ldb(0x44,0x1fa4);a.cmpb(0x44,0);a.label('admit_return');a.emit(0xf0)
# Native Exit already pops this popup. Queue native event0B afterwards: it
# redraws the restored mode0 parent using single-level pop/reopen, preserving
# its mode2 ancestor. Extra event2 would recursively discard that ancestor.
a.label('exit');prologue();a.ld(0x44,C+90);a.st(0,C+90);a.cmp(0x44,0);a.cond(0xd7,'exit_done')
a.byte(0x48,0x0b);a.call('event')
a.label('exit_done');epilogue()
a.label('init');prologue();a.imm(0x20,C+16);a.imm(0x22,38);a.label('init_context_reset');a.emit(0xc2,0x21,0);a.emit(5,0x22);a.cond(0xd7,'init_context_reset');a.call('render');a.call('clear_draw');a.stb(0,0x2152);a.stb(0,0x22e8);highlight();epilogue()
a.label('update');prologue();a.ldb(0x44,0x2476);a.cmpb(0x44,0);a.cond(0xdf,'lcd_update');a.ldb(0x44,0x22e8);a.cmpb(0x44,0);a.cond(0xdf,'update_end');a.stb(0,0x22e8);native(0x9460,0x196);a.label('update_end');epilogue()
a.label('lcd_update');a.ldb(0x44,0x22e8);a.cmpb(0x44,0);a.cond(0xdf,'lcd_scroll_keys');a.stb(0,0x22e8);a.ldb(0xb7,0x2152);a.jmp('body_0')
a.label('lcd_scroll_keys');a.ld(0x44,MODE);a.cmp(0x44,3);a.cond(0xdf,'lcd_update_end');a.ld(0x44,SCROLL);a.cmpb(0xe0,0x29);a.cond(0xd7,'lcd_scroll_down');a.cmp(0x44,0);a.cond(0xdf,'lcd_update_end');a.emit(5,0x44);a.jmp('lcd_scroll_changed')
a.label('lcd_scroll_down');a.cmpb(0xe0,0x26);a.cond(0xd7,'lcd_update_end');a.cmp(0x44,2);a.cond(0xdb,'lcd_update_end');a.emit(7,0x44)
a.label('lcd_scroll_changed');a.st(0x44,SCROLL);a.call('lcd_draw')
a.label('lcd_update_end');epilogue()

def lcd(target):
 a.imm(0x1c,0x3b);a.imm(0x1e,target);a.call('ce14');a.imm(0x1c,15);a.st(0x1c,0x10a)

a.label('lcd_draw');a.imm(0x48,TMP);a.imm(0x4a,25);a.byte(0x44,32)
a.label('lcd_blank_buffer');a.emit(0xc6,0x49,0x44,5,0x4a);a.cond(0xd7,'lcd_blank_buffer');a.emit(0xc6,0x48,0)
a.imm(0x20,0)
a.label('lcd_clear_row');a.byte(0xf0,0);a.emit(0xb0,0x20,0xf1);a.byte(0xf2,0);a.imm(0xe2,TMP);lcd(0x64fa);a.emit(7,0x20);a.cmp(0x20,8);a.cond(0xd7,'lcd_clear_row')
a.imm(0xe2,RESOURCE+labels+3);a.ld(0x44,MODE);a.cmp(0x44,3);a.cond(0xd7,'lcd_caption_chosen');a.imm(0xe2,extra_strings['confirm']);a.label('lcd_caption_chosen');a.byte(0xf0,0);a.byte(0xf1,0);a.byte(0xf2,0);lcd(0x64fa)
a.ld(0x44,MODE);a.cmp(0x44,1);a.cond(0xdf,'lcd_show_target');a.cmp(0x44,3);a.cond(0xd7,'lcd_title_done');a.label('lcd_show_target');a.byte(0x44,67);a.stb(0x44,TMP);a.byte(0x44,68);a.stb(0x44,TMP+1);a.ld(0x44,TARGET);plus(0x44,48);a.stb(0x44,TMP+2);a.stb(0,TMP+3);a.imm(0xe2,TMP);a.byte(0xf0,17);a.byte(0xf1,0);a.byte(0xf2,0);lcd(0x64fa)
a.label('lcd_title_done');a.ld(0x22,SCROLL)
# Nine owned32-byte rows have a36-byte stride. Compute scroll*36 without MUL.
a.mov(0x24,0x22);a.emit(0x09,5,0x22,0x09,2,0x24,0x64,0x24,0x22);plus(0x22,text[0]);a.imm(0x20,1)
a.label('lcd_text_row');a.mov(0x48,0x22);a.imm(0x4a,TMP);a.imm(0x4c,21)
a.label('lcd_copy_char');a.emit(0xb2,0x49,0x44,0xc6,0x4b,0x44,5,0x4c);a.cond(0xd7,'lcd_copy_char');a.stb(0,TMP+21)
a.byte(0xf0,3);a.emit(0xb0,0x20,0xf1);a.byte(0xf2,0);a.imm(0xe2,TMP);lcd(0x64fa);plus(0x22,36);a.emit(7,0x20);a.cmp(0x20,8);a.cond(0xd7,'lcd_text_row')
a.byte(0xf0,1);a.ldb(0xf1,0x2152);a.emit(0x75,1,0xf1);a.byte(0xf2,0);a.byte(0xf3,0xc2);lcd(0x62c7);a.emit(0xf0)

# Clear the enlarged popup with native CRT primitives, then redraw its labels.
def crt(target):
 a.imm(0x1c,0x4b);a.imm(0x1e,target);a.call('ce14');a.imm(0x1c,15);a.st(0x1c,0x10a)
a.label('clear_draw');a.ldb(0x44,0x2476);a.cmpb(0x44,0);a.cond(0xd7,'crt_draw');a.call('lcd_draw');a.emit(0xf0);a.label('crt_draw');a.imm(0x20,3)
a.label('clear_line');a.byte(0xf0,0);a.emit(0xb0,0x20,0xf1);a.byte(0xf2,0xc0);a.byte(0x48,0);a.byte(0xf4,40);crt(0x4aee)
a.imm(0x22,40);a.byte(0xf0,0);a.emit(0xb0,0x20,0xf1)
a.label('clear_character');a.call('service');a.byte(0xf2,0xc0);a.byte(0xf3,32);crt(0x42a7);a.emit(5,0x22);a.cond(0xd7,'clear_character')
a.emit(7,0x20);a.cmp(0x20,25);a.cond(0xd7,'clear_line')
a.ld(0x44,MODE);a.imm(0xe2,extra_strings['collections']);a.cmp(0x44,0);a.cond(0xdf,'title_chosen');a.imm(0xe2,extra_strings['disk']);a.cmp(0x44,2);a.cond(0xdf,'title_chosen')
a.ld(0x44,TARGET)
for target in [1,2,3,6]:
 a.imm(0xe2,extra_strings['id'+str(target)]);a.cmp(0x44,target);a.cond(0xdf,'title_chosen')
a.imm(0xe2,RESOURCE+labels+3)
a.label('title_chosen');a.byte(0xf0,3);a.byte(0xf1,3);a.byte(0xf2,0x80);crt(0x4550)
a.ld(0x44,MODE);a.imm(0xe2,extra_strings['help0']);a.cmp(0x44,0);a.cond(0xdf,'help_chosen');a.imm(0xe2,extra_strings['help2']);a.cmp(0x44,2);a.cond(0xdf,'help_chosen');a.imm(0xe2,extra_strings['help1'])
a.label('help_chosen');a.byte(0xf0,0);a.byte(0xf1,24);a.byte(0xf2,0xf0);crt(0x4550)
a.imm(0x20,5);a.imm(0x22,text[0])
a.label('draw_line');a.byte(0xf0,3);a.emit(0xb0,0x20,0xf1);a.byte(0xf2,0xf0);a.mov(0xe2,0x22);crt(0x4550);plus(0x22,36);plus(0x20,2);a.cmp(0x20,23);a.cond(0xd7,'draw_line');a.emit(0xf0)
a.label('render');a.st(0,SCROLL);a.imm(0x20,0);a.imm(0x22,text[0]);a.ld(0x24,MODE)
a.label('render_row');a.mov(0x48,0x22);a.imm(0x4a,32);a.byte(0x44,32)
a.label('blank_row');a.emit(0xc6,0x49,0x44,5,0x4a);a.cond(0xd7,'blank_row')
a.cmp(0x24,3);a.cond(0xdf,'confirm_label');a.cmp(0x24,2);a.cond(0xdf,'native_label');a.cmp(0x24,0);a.cond(0xdf,'collection_label');a.cmp(0x20,7);a.cond(0xdf,'previous_label');a.cmp(0x20,8);a.cond(0xdf,'next_label')
a.ld(0x44,FIRST);a.emit(0x64,0x20,0x44);a.ld(0x46,COUNT);a.emit(0x88,0x46,0x44);a.cond(0xdb,'render_next');a.mov(0x44,0x20);rowptr();a.mov(0x48,0x44);a.jmp('copy_label')
a.label('confirm_label');a.cmp(0x20,4);a.cond(0xdf,'confirm_target_label');a.cmp(0x20,2);a.cond(0xdf,'confirm_mount_label');a.cmp(0x20,3);a.cond(0xdf,'confirm_back_label');a.cmp(0x20,1);a.cond(0xd9,'render_next')
a.clr(0x44);a.ldb(0x44,C+42);a.ld(0x46,FIRST);a.emit(0x68,0x46,0x44);a.cmp(0x44,7);a.cond(0xdb,'render_next');rowptr();a.mov(0x48,0x44);a.mov(0x44,0x20);a.emit(0x09,4,0x44,0x64,0x44,0x48);a.mov(0x4a,0x22);a.imm(0x4c,16)
a.label('confirm_name_copy');a.emit(0xb2,0x49,0x44);a.label('confirm_filter');a.cmpb(0x44,0);a.cond(0xdf,'confirm_space');a.cmpb(0x44,31);a.cond(0xd1,'confirm_invalid');a.cmpb(0x44,126);a.cond(0xd1,'confirm_emit');a.label('confirm_invalid');a.byte(0x44,63);a.jmp('confirm_emit');a.label('confirm_space');a.byte(0x44,32);a.label('confirm_emit');a.emit(0xc6,0x4b,0x44,5,0x4c);a.cond(0xd7,'confirm_name_copy');a.jmp('render_next')
a.label('confirm_target_label');a.mov(0x48,0x22);a.imm(0x44,0x4443);a.emit(0xc2,0x49,0x44);a.ld(0x44,TARGET);plus(0x44,48);a.emit(0xc6,0x48,0x44);a.jmp('render_next')
a.label('confirm_mount_label');a.imm(0x48,extra_strings['mount']);a.jmp('copy_label')
a.label('confirm_back_label');a.imm(0x48,extra_strings['back']);a.jmp('copy_label')
a.label('native_label');a.mov(0x48,0x20);plus(0x48,MENU);a.emit(0xae,0x48,0x48);plus(0x48,MENU);a.jmp('copy_label')
a.label('collection_label');a.cmp(0x20,5);a.cond(0xd7,'ordinary_collection');a.imm(0x48,MENU+86);a.jmp('copy_label');a.label('ordinary_collection');a.cmp(0x20,4);a.cond(0xdf,'error_label');a.cmp(0x20,3);a.cond(0xd9,'render_next');a.mov(0x48,0x20);a.emit(0x09,4,0x48);plus(0x48,RESOURCE+blank+5);a.jmp('copy_label')

a.label('error_label');a.ld(0x44,ERROR);a.cmp(0x44,0);a.cond(0xdf,'render_next');a.imm(0x48,RESOURCE+message_uncertain);a.ld(0x46,C+86);a.cmp(0x46,0);a.cond(0xd7,'copy_label');a.imm(0x48,RESOURCE+message_error);a.cmp(0x44,11);a.cond(0xd7,'error_before_switch');a.imm(0x48,RESOURCE+message_busy);a.jmp('copy_label')
a.label('error_before_switch');a.cmp(0x44,7);a.cond(0xd7,'copy_label');a.imm(0x48,RESOURCE+message_cancel);a.jmp('copy_label')
a.label('previous_label');a.ld(0x44,FIRST);a.imm(0x48,RESOURCE+blank+69);a.cmp(0x44,0);a.cond(0xd7,'copy_label');a.imm(0x48,RESOURCE+blank+85);a.jmp('copy_label')
a.label('next_label');a.imm(0x48,RESOURCE+blank+101)
a.label('copy_label');a.mov(0x4a,0x22);a.imm(0x4c,32)
a.label('copy_char');a.emit(0xb2,0x49,0x44);a.cmpb(0x44,0);a.cond(0xdf,'render_next');a.cmpb(0x44,31);a.cond(0xd1,'replace_char');a.cmpb(0x44,126);a.cond(0xd1,'emit_char');a.label('replace_char');a.byte(0x44,63)
a.label('emit_char');a.emit(0xc6,0x4b,0x44,5,0x4c);a.cond(0xd7,'copy_char')
a.label('render_next');plus(0x22,36);a.emit(7,0x20);a.cmp(0x20,9);a.cond(0xd7,'render_row');a.emit(0xf0)

a.label('discover');a.byte(0x44,0x12);a.imm(0x2e,96);a.call('exchange');a.cmp(0x3e,0);a.cond(0xd7,'discover_return')
a.cmp(0x30,45);a.cond(0xd3,'bad_reply')
for off,value in [(36,0x6c42),(38,0x6575),(40,0x4353),(42,0x4953)]:
 a.ld(0x44,B+off);a.cmp(0x44,value);a.cond(0xd7,'bad_reply')
a.mov(0x48,0x30);plus(0x48,B-1);a.emit(0xb2,0x48,0x44);a.cmpb(0x44,0);a.cond(0xd7,'bad_reply')
a.byte(0x44,0x1a);a.imm(0x2e,48);a.call('exchange');a.cmp(0x3e,0);a.cond(0xd7,'discover_return');a.cmp(0x30,48);a.cond(0xd7,'bad_reply')
a.ld(0x44,B);a.cmp(0x44,47);a.cond(0xd7,'bad_reply');a.ldb(0x44,B+3);a.cmpb(0x44,0);a.cond(0xd7,'bad_reply')
a.imm(0x48,B+4);a.imm(0x4a,RESOURCE+signature);a.imm(0x4c,44)
a.label('vendor_compare');a.emit(0xb2,0x49,0x44,0xb2,0x4b,0x46,0x98,0x44,0x46);a.cond(0xd7,'bad_reply');a.emit(5,0x4c);a.cond(0xd7,'vendor_compare')
a.label('discover_return');a.emit(0xf0)

a.label('get_catalog');a.stb(0,C+82);a.byte(0x44,0xda);a.imm(0x2e,1);a.call('exchange');a.cmp(0x3e,0);a.cond(0xd7,'catalog_return');a.cmp(0x30,1);a.cond(0xd7,'bad_reply');a.clr(0x44);a.ldb(0x44,B);a.cmp(0x44,100);a.cond(0xd9,'bad_reply');a.st(0x44,COUNT);a.ld(0x46,FIRST);a.emit(0x88,0x44,0x46);a.cond(0xd3,'page_origin_ok');a.st(0,FIRST);a.label('page_origin_ok');a.mov(0x2e,0x44);a.emit(0x09,5,0x44,0x09,3,0x2e,0x64,0x44,0x2e);a.st(0x2e,C+88);a.byte(0x44,0xd7);a.call('exchange');a.cmp(0x3e,0);a.cond(0xd7,'catalog_return');a.ldb(0x44,C+82);a.cmpb(0x44,0);a.cond(0xd7,'bad_reply');a.ld(0x44,C+88);a.emit(0x88,0x44,0x30);a.cond(0xd7,'bad_reply');a.label('catalog_return');a.emit(0xf0)
a.label('mount');a.st(0,C+84);a.byte(0x44,0xd8);a.imm(0x2e,0);a.call('exchange');a.st(0x58,C+86);a.cmp(0x3e,0);a.cond(0xd7,'mount_return')
a.imm(0x4e,4)
a.label('ready_loop');a.call('ready_delay');a.cmp(0x3e,0);a.cond(0xd7,'mount_return');a.byte(0x44,0);a.clr(0x2e);a.call('exchange');a.cmp(0x3e,0);a.cond(0xdf,'mounted');a.cmp(0x3e,7);a.cond(0xdf,'mount_return');a.byte(0x44,3);a.imm(0x2e,18);a.call('exchange');a.emit(5,0x4e);a.cond(0xd7,'ready_loop');a.jmp('bad_reply')
a.label('mounted');a.byte(0x44,0x25);a.imm(0x2e,8);a.call('exchange');a.cmp(0x3e,0);a.cond(0xd7,'mount_return');a.cmp(0x30,8);a.cond(0xd7,'bad_reply');a.label('mount_return');a.emit(0xf0)

# Pace readiness probes20ms apart, at most4 attempts. Sample Exit throughout;
# bound the loop by both TIMER1 and a finite poll budget if the timer stalls.
a.label('ready_delay');a.mov(0x52,0x0a);a.imm(0x5a,65535)
a.label('ready_delay_poll');a.call('service');a.ld(0x44,C+16);a.cmp(0x44,0);a.cond(0xd7,'ready_cancel');a.mov(0x44,0x0a);a.emit(0x68,0x52,0x44);a.cmp(0x44,20000);a.cond(0xdb,'ready_delay_done');a.emit(5,0x5a);a.cond(0xd7,'ready_delay_poll');a.imm(0x3e,4);a.emit(0xf0)
a.label('ready_cancel');a.imm(0x3e,7);a.emit(0xf0)
a.label('ready_delay_done');a.clr(0x3e);a.emit(0xf0)

a.label('exchange');a.stb(0x44,C+72);a.st(0,CDB);a.st(0,CDB+2);a.st(0,CDB+4);a.st(0,CDB+6);a.st(0,CDB+8);a.stb(0x44,CDB)
a.cmpb(0x44,0xd8);a.cond(0xd7,'not_switch');a.ldb(0x44,C+42);a.stb(0x44,CDB+1)
a.label('not_switch');a.ldb(0x44,C+72);a.imm(0x2a,10);a.cmpb(0x44,3);a.cond(0xd7,'not_sense');a.byte(0x44,18);a.stb(0x44,CDB+4);a.imm(0x2a,6)
a.label('not_sense');a.ldb(0x44,C+72);a.cmpb(0x44,0);a.cond(0xd7,'probe_six');a.imm(0x2a,6);a.jmp('wire');a.label('probe_six')
a.cmpb(0x44,0x12);a.cond(0xdf,'six_alloc');a.cmpb(0x44,0x1a);a.cond(0xd7,'wire');a.byte(0x44,8);a.stb(0x44,CDB+1);a.byte(0x44,0x31);a.stb(0x44,CDB+2)
a.label('six_alloc');a.stb(0x2e,CDB+4);a.imm(0x2a,6)
a.label('wire');a.ld(0x52,FIRST);a.mov(0x4a,0x52);plus(0x4a,7);a.clr(0x4c);a.clr(0x5e);a.imm(0x28,CDB);a.imm(0x2c,B);a.clr(0x30);a.clr(0x34);a.clr(0x36);a.clr(0x3e);a.clr(0x58);a.imm(0x40,0xffff);a.mov(0x32,0x0a);a.mov(0x38,0x32);a.mov(0x5a,0x32);a.imm(0x3a,65535);a.imm(0x50,1);a.ld(0x44,TARGET);a.emit(0x19,0x44,0x50);a.byte(0x54,0);a.byte(0x5c,0)
# Capture the same caller interrupt/data context used by the qualified sender.
a.ldb(0x44,0x115);a.stb(0x44,C+14);a.emit(0x71,0xef,0x44);a.stb(0x44,0x115);a.call('transaction');a.call('cancel_scan');a.ldb(0x44,C+14);a.stb(0x44,0x115);a.st(0x40,C+46)
a.cmp(0x3e,0);a.cond(0xd7,'exchange_return');a.cmpb(0x40,0);a.cond(0xd7,'bad_reply');a.ld(0x44,C+16);a.cmp(0x44,0);a.cond(0xdf,'exchange_return');a.imm(0x3e,7);a.label('exchange_return');a.emit(0xf0)
a.label('bad_reply');a.imm(0x3e,9);a.emit(0xf0)
source=(SOURCE/'asmkit.py').read_text();fragment=source[source.index(" a.label('transaction')"):source.index(" a.label('code_end')")]
# Native context was captured by the outer UI callback before any transport.
# UI callbacks are masked for this first scoped browser test; no external IRQ enable.
# Original caller flags/data bank captured below; no unconditional IRQ enable.
fragment=fragment.replace("a.ldb(0x44,0xe416);a.emit(0xc6,0x2d,0x44)", "a.ldb(0x44,CONTROL+72);a.cmpb(0x44,0xd7);a.cond(0xd7,'retain_byte');a.cmp(0x5e,0);a.cond(0xd7,'not_listing_index');a.label('check_listing_index');a.ldb(0x44,0xe416);a.emit(0x98,0x4c,0x44);a.cond(0xdf,'listing_index_ok');a.byte(0x44,1);a.stb(0x44,CONTROL+82);a.label('listing_index_ok');a.emit(7,0x4c);a.jmp('discard_listing_byte');a.label('not_listing_index');a.cmp(0x5e,1);a.cond(0xdf,'discard_listing_byte');a.cmp(0x5e,34);a.cond(0xd3,'retain_listing_byte');a.label('discard_listing_byte');a.emit(7,0x5e);a.cmp(0x5e,40);a.cond(0xd7,'data_ack');a.clr(0x5e);a.jmp('data_ack');a.label('retain_listing_byte');a.emit(0x88,0x52,0x4c);a.cond(0xd1,'discard_listing_byte');a.emit(0x88,0x4a,0x4c);a.cond(0xd9,'discard_listing_byte');a.emit(7,0x5e);a.label('retain_byte');a.ldb(0x44,0xe416);a.emit(0xc6,0x2d,0x44)")
# Idle time excludes the bounded service window; total elapsed/poll budgets do not.
fragment=fragment.replace(" a.call('cancel_scan')\n a.ld(0x44,CONTROL+8)", " a.call('cancel_scan')\n a.imm(0x44,0x8020);a.st(0x44,CONTROL+26);a.label('service_clock_start');a.mov(0x44,0x0a);a.st(0x44,CONTROL+28)\n a.ld(0x44,CONTROL+8)")
fragment=fragment.replace(" for r in reversed(saved):a.emit(0xcc,r)", " for r in reversed(saved):\n  a.emit(0xcc,r)\n  if r==0x38:\n   a.st(0,CONTROL+26);a.label('service_clock_end');a.mov(0x36,0x0a);a.ld(0x34,CONTROL+28);a.emit(0x68,0x34,0x36);a.label('service_progress_adjust');a.emit(0x64,0x36,0x38)")
# Queue continuation only after the service returns masked, rather than from its ISR.
fragment=fragment.replace(" a.imm(0x48,15);a.label('service_probe_bank');a.st(0x48,0x10a)"," a.imm(0x48,15);a.label('service_probe_bank');a.st(0x48,0x10a)\n a.emit(0x3a,0x7b,3);a.jmp('service_ring_compare');a.jmp('service_ring_reschedule')\n a.label('service_ring_compare');a.emit(0x88,0x70,0x6e);a.cond(0xdf,'service_ring_done')\n a.label('service_ring_reschedule');a.emit(0x91,0x10,0x7b,0xb1,0x39,6,0x45,10,0,0x0a,4)\n a.label('service_ring_done')")
exec('if True:\n'+fragment,dict(a=a,CONTROL=C,saved=saved))
a.label('common_prologue');a.emit(0xcb,1,0x0a,1)
for r in ALL_SAVED:a.emit(0xc8,r)
a.byte(0x14,0);a.imm(0x1c,15);a.st(0x1c,0x10a)
# Common frame before the dispatcher return:70 register bytes, DATA1+70,
# original RW1E+72, saved WSR/MASK1+74, saved PSW/MASK0+76.
for offset,dest in [(70,6),(74,10),(76,8)]:
 a.emit(0xa3,0x19);a.word(offset);a.emit(0x44);a.st(0x44,C+dest)
a.label('common_return_literal');a.emit(0xc9,0,0);a.emit(0xe3,0x1e)
a.label('common_epilogue')
for r in reversed(ALL_SAVED):a.emit(0xcc,r)
a.emit(0xcf,1,0x0a,1,0xcc,0x1e,0xf5,0xf0)
a.label('event');a.emit(0xef,0,0,0xf0);a.label('ce14');a.emit(0xef,0,0,0xf0);a.label('cded');a.emit(0xef,0,0,0xf0);a.label('screen');a.emit(0xef,0,0,0xf0);a.label('code_end')
code=bytearray(a.finish())
for name,target in [('event',0x2080),('ce14',0xce14),('cded',0xcded),('screen',0xf0a8)]:
 pos=a.labels[name]-0x8480;struct.pack_into('<H',code,pos+1,(target-(a.labels[name]+3))&65535)
for n in callback_bodies:
 pos=a.labels[f'entry_literal_{n}']-0x8480;struct.pack_into('<H',code,pos+1,a.labels[f'body_{n}'])
pos=a.labels['common_return_literal']-0x8480;struct.pack_into('<H',code,pos+1,a.labels['common_epilogue'])
ins=pypcode.Context('MCS96:LE:16:default').disassemble(bytes(code),base_address=0x8480).instructions;assert sum(i.length for i in ins)==len(code)
for row in range(9):struct.pack_into('<HH',blob,tuples+row*4,a.labels['action'],15)
for i in range(10):struct.pack_into('<HH',blob,callbacks+i*4,0x8000,0x171)
for i,name in [(0,'init'),(1,'update'),(2,'exit')]:struct.pack_into('<HH',blob,callbacks+i*4,a.labels[name],15)
blob.extend(bytes([1,2,3,6]))
for s in ['ISO A (ID 1)','IMG (ID 2)','ISO B (ID 3)','ISO C (ID 6)','Previous','Collections','Next']:blob.extend(s.encode().ljust(16,b'\0'))
assert len(blob)==signature
blob.extend(bytes([0x31,42])+b'BlueSCSI is the BEST STOLEN FROM BLUESCSI\0')
assert len(blob)==message_cancel
for off,value in [(message_cancel,b'Cancelled'),(message_uncertain,b'Mount uncertain; select again'),(message_error,b'SCSI error'),(message_busy,b'Busy')]:
 assert len(blob)==off,(len(blob),off)
 blob.extend(value+b'\0')
assert len(blob)<=0x3f0
lcd_source=0x91da;lcd_end=0x92ae;lcd_file=0x4800+(0x219<<10)+(lcd_source&0x3fff)
lcd_blob=bytearray(original[lcd_file:lcd_file+lcd_end-lcd_source]);delta=LCD_UI-lcd_source
for off in list(range(0,16,2))+[0x9230-lcd_source,0x9232-lcd_source]:
 value=struct.unpack_from('<H',lcd_blob,off)[0];struct.pack_into('<H',lcd_blob,off,value+delta)
lcd_blob[16:26]=b'Image Lib\0'
for i in range(10):struct.pack_into('<HH',lcd_blob,0x9286-lcd_source+i*4,0x8000,0x171)
for i,name in [(0,'init'),(1,'update'),(2,'exit')]:struct.pack_into('<HH',lcd_blob,0x9286-lcd_source+i*4,a.labels[name],15)
for i in range(7):struct.pack_into('<HH',lcd_blob,0x9268-lcd_source+i*4,a.labels['action'],15)
image=bytearray(original);image[0x9e50:0x9e50+len(lcd_blob)]=lcd_blob
struct.pack_into('<HH',image,0x4800+(0x219<<10)+4*0xf5,15,LCD_UI)
image[0x9d00:0x9d00+len(extra)]=extra;image[0x8880:0x8880+len(code)]=code;image[0xa0d0:0xa0d0+len(blob)]=blob;struct.pack_into('<HH',image,0x4800+(0x219<<10)+4*0xf4,15,RESOURCE_UI)
menu=bytearray(9)
for i,name in enumerate(['Load','Save','Copy','Delete','Utility','Save System','Optimize','Convert Load','Vol. Dump FD']):
 menu[i]=len(menu);menu.extend(name.encode()+b'\0')
assert len(menu)==86
menu.extend(b'Disk options\0');menu.extend(b'\0');assert len(menu)==100
image[0xa41c:0xa480]=menu
assert 0x4080+len(code)<=0x5500,(len(code),hex(0x4080+len(code)))
from parser_quota import patch_parser
assert 0x4080+len(code)<=0x5100
quota=patch_parser(image)
with (P/'browser-linked.img').open('xb') as f:f.write(image)
(P/'build-linked.json').write_text(json.dumps(dict(parser_quota=quota,sha256=hashlib.sha256(image).hexdigest(),code_bytes=len(code),resource_bytes=len(blob),lcd_bytes=len(lcd_blob)+26,lcd_ui=LCD_UI,extra_bytes=len(extra),extra_strings=extra_strings,labels=a.labels,text_addresses=text,resource_file=0xa0d0,code_file=0x8880,decoded=[dict(pc=i.addr.offset,bytes=bytes(code[i.addr.offset-0x8480:i.addr.offset-0x8480+i.length]).hex(),text=i.mnem+' '+i.body) for i in ins]),indent=2))
print('code',len(code),'resources',len(blob),'instructions',len(ins))
