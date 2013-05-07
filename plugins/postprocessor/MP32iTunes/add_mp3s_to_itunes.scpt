FasdUAS 1.101.10   ��   ��    k             l     ��  ��    p j this script will go thru all sub folders (recursively) and look for mp3s it will add these mp3s to iTunes     � 	 	 �   t h i s   s c r i p t   w i l l   g o   t h r u   a l l   s u b   f o l d e r s   ( r e c u r s i v e l y )   a n d   l o o k   f o r   m p 3 s   i t   w i l l   a d d   t h e s e   m p 3 s   t o   i T u n e s   
  
 l     ��  ��    K E after all mp3s where added iTunes "Match" will be updated (optional)     �   �   a f t e r   a l l   m p 3 s   w h e r e   a d d e d   i T u n e s   " M a t c h "   w i l l   b e   u p d a t e d   ( o p t i o n a l )      l     ��  ��    * $ all mps3 will be deleted (optional)     �   H   a l l   m p s 3   w i l l   b e   d e l e t e d   ( o p t i o n a l )      l     ��  ��    ? 9 for every added files a growl message is send (optional)     �   r   f o r   e v e r y   a d d e d   f i l e s   a   g r o w l   m e s s a g e   i s   s e n d   ( o p t i o n a l )      l     ��  ��    L F please see propertys bellow for settings. 0 = Off / No. 1 = ON / Yes      �   �   p l e a s e   s e e   p r o p e r t y s   b e l l o w   f o r   s e t t i n g s .   0   =   O f f   /   N o .   1   =   O N   /   Y e s        l     ��   !��     � � USAGE: set this script as a folder action for a folder you want to watch or use it from the command line with: osascript add_mp3s_to_itunes.scpt <folder_to_process>    ! � " "J   U S A G E :   s e t   t h i s   s c r i p t   a s   a   f o l d e r   a c t i o n   f o r   a   f o l d e r   y o u   w a n t   t o   w a t c h   o r   u s e   i t   f r o m   t h e   c o m m a n d   l i n e   w i t h :   o s a s c r i p t   a d d _ m p 3 s _ t o _ i t u n e s . s c p t   < f o l d e r _ t o _ p r o c e s s >   # $ # l     �� % &��   % � � for use with sabnzbd create a "sabToitunes.py" python script and place it next to this file. the contense is as follows (without the leading "(*" and trailing "*)"):    & � ' 'L   f o r   u s e   w i t h   s a b n z b d   c r e a t e   a   " s a b T o i t u n e s . p y "   p y t h o n   s c r i p t   a n d   p l a c e   i t   n e x t   t o   t h i s   f i l e .   t h e   c o n t e n s e   i s   a s   f o l l o w s   ( w i t h o u t   t h e   l e a d i n g   " ( * "   a n d   t r a i l i n g   " * ) " ) : $  ( ) ( l      �� * +��   *=7
#!/usr/bin/python

import sys, os
from subprocess import call
if len(sys.argv) < 2:
    print "No folder supplied - is this being called from SABnzbd?"
    sys.exit()
else:
    scriptFile = os.path.join(os.path.dirname(sys.argv[0]), "add_mp3s_to_itunes.scpt")
    call(['osascript', scriptFile, sys.argv[1]])

    + � , ,n 
 # ! / u s r / b i n / p y t h o n 
 
 i m p o r t   s y s ,   o s 
 f r o m   s u b p r o c e s s   i m p o r t   c a l l 
 i f   l e n ( s y s . a r g v )   <   2 : 
         p r i n t   " N o   f o l d e r   s u p p l i e d   -   i s   t h i s   b e i n g   c a l l e d   f r o m   S A B n z b d ? " 
         s y s . e x i t ( ) 
 e l s e : 
         s c r i p t F i l e   =   o s . p a t h . j o i n ( o s . p a t h . d i r n a m e ( s y s . a r g v [ 0 ] ) ,   " a d d _ m p 3 s _ t o _ i t u n e s . s c p t " ) 
         c a l l ( [ ' o s a s c r i p t ' ,   s c r i p t F i l e ,   s y s . a r g v [ 1 ] ] ) 
 
 )  - . - l     �� / 0��   / R L NOTE: this script will log stuff in "~/Library/Logs/AppleScript-events.log"    0 � 1 1 �   N O T E :   t h i s   s c r i p t   w i l l   l o g   s t u f f   i n   " ~ / L i b r a r y / L o g s / A p p l e S c r i p t - e v e n t s . l o g " .  2 3 2 l     �� 4 5��   4 � � NOTE: the update_match currently only works with system language "en" or "de", because i dont know the menu names for other languages but they can be added    5 � 6 68   N O T E :   t h e   u p d a t e _ m a t c h   c u r r e n t l y   o n l y   w o r k s   w i t h   s y s t e m   l a n g u a g e   " e n "   o r   " d e " ,   b e c a u s e   i   d o n t   k n o w   t h e   m e n u   n a m e s   f o r   o t h e r   l a n g u a g e s   b u t   t h e y   c a n   b e   a d d e d 3  7 8 7 l      9 : ; 9 j     �� <�� 0 update_match   < m     ����  : ` Z should i tell to itunes update match ? this might bring itunes into front (GUI scripting)    ; � = = �   s h o u l d   i   t e l l   t o   i t u n e s   u p d a t e   m a t c h   ?   t h i s   m i g h t   b r i n g   i t u n e s   i n t o   f r o n t   ( G U I   s c r i p t i n g ) 8  > ? > l      @ A B @ j    �� C�� 0 delete_mp3s   C m    ����  A ) # should the added mp3s be deleted ?    B � D D F   s h o u l d   t h e   a d d e d   m p 3 s   b e   d e l e t e d   ? ?  E F E l      G H I G j    �� J�� 0 send_growl_notifications   J m    ����   H 9 3 should growl notifications be send for each file ?    I � K K f   s h o u l d   g r o w l   n o t i f i c a t i o n s   b e   s e n d   f o r   e a c h   f i l e   ? F  L M L l      N O P N j   	 �� Q�� 0 boxcar_user_email   Q m   	 
 R R � S S " l a d 1 3 3 7 @ g m a i l . c o m O ) # send boxcar notification on finish    P � T T F   s e n d   b o x c a r   n o t i f i c a t i o n   o n   f i n i s h M  U V U l      W X Y W j    �� Z�� (0 delay_time_seconds DELAY_TIME_SECONDS Z m    ����  X 3 - How long to wait between checking file size.    Y � [ [ Z   H o w   l o n g   t o   w a i t   b e t w e e n   c h e c k i n g   f i l e   s i z e . V  \ ] \ j    �� ^�� 0 myfiletypes myFiletypes ^ J     _ _  `�� ` m     a a � b b  . m p 3��   ]  c d c l      e f g e j    �� h�� 0 enable_dialog   h m    ����   f  y should there be a question dialog at all? dont know why you would wan that but its kinda a leftover from the development    g � i i �   s h o u l d   t h e r e   b e   a   q u e s t i o n   d i a l o g   a t   a l l ?   d o n t   k n o w   w h y   y o u   w o u l d   w a n   t h a t   b u t   i t s   k i n d a   a   l e f t o v e r   f r o m   t h e   d e v e l o p m e n t d  j k j l      l m n l j    �� o�� 0 dialog_timeout   o m    ����  m c ] set the amount of time before dialogs auto-answer. it will say "no" after the amount of time    n � p p �   s e t   t h e   a m o u n t   o f   t i m e   b e f o r e   d i a l o g s   a u t o - a n s w e r .   i t   w i l l   s a y   " n o "   a f t e r   t h e   a m o u n t   o f   t i m e k  q r q l      s t u s j    �� v�� 0 test_folder   v m     w w � x x B H D D : l a d 1 3 3 7 : D e s k t o p : a d d _ m p 3 _ t e s t : t b \ process this folder if no argument is given great for testing from within the script editor    u � y y �   p r o c e s s   t h i s   f o l d e r   i f   n o   a r g u m e n t   i s   g i v e n   g r e a t   f o r   t e s t i n g   f r o m   w i t h i n   t h e   s c r i p t   e d i t o r r  z { z l      | } ~ | j    �� �� 0 
more_debug    m    ����   }   log more information    ~ � � � *   l o g   m o r e   i n f o r m a t i o n {  � � � l     �� � ���   � : 4----------------- no need to edit the folowing stuff    � � � � h - - - - - - - - - - - - - - - - -   n o   n e e d   t o   e d i t   t h e   f o l o w i n g   s t u f f �  � � � l      � � � � j     "�� ��� 0 
out_buffer   � m     ! � � � � �   �  y this does not concern you !! (its an output buffer with all log messages that is returned at the end for terminal usage)    � � � � �   t h i s   d o e s   n o t   c o n c e r n   y o u   ! !   ( i t s   a n   o u t p u t   b u f f e r   w i t h   a l l   l o g   m e s s a g e s   t h a t   i s   r e t u r n e d   a t   t h e   e n d   f o r   t e r m i n a l   u s a g e ) �  � � � l      � � � � j   # %�� ��� 0 number_of_mp3s   � m   # $����   � 0 * counting the mp3s added to iTunes per run    � � � � T   c o u n t i n g   t h e   m p 3 s   a d d e d   t o   i T u n e s   p e r   r u n �  � � � l      � � � � j   & *�� ��� "0 scriptgrowlname scriptGrowlName � m   & ) � � � � � 2 A d d   m p 3 s   t o   i T u n e s   s c r i p t � > 8 the name that will appear in the growl application list    � � � � p   t h e   n a m e   t h a t   w i l l   a p p e a r   i n   t h e   g r o w l   a p p l i c a t i o n   l i s t �  � � � l     �� � ���   �   logging function from    � � � � ,   l o g g i n g   f u n c t i o n   f r o m �  � � � l     �� � ���   � C = http://hints.macworld.com/article.php?story=2004121710493371    � � � � z   h t t p : / / h i n t s . m a c w o r l d . c o m / a r t i c l e . p h p ? s t o r y = 2 0 0 4 1 2 1 7 1 0 4 9 3 3 7 1 �  � � � i   + . � � � I      �� ����� 0 	log_event   �  ��� � o      ���� 0 
themessage  ��  ��   � k     - � �  � � � r      � � � b      � � � b     	 � � � l 
    ����� � l     ����� � I    �� � �
�� .sysoexecTEXT���     TEXT � l 	    ����� � m      � � � � � 4 d a t e     + ' % Y - % m - % d   % H : % M : % S '��  ��   � �� ���
�� 
rtyp � m    ��
�� 
TEXT��  ��  ��  ��  ��   � m     � � � � �    � o   	 
���� 0 
themessage   � o      ���� 0 theline theLine �  � � � l   �� � ���   � _ Y the line break in next lines "" is not a misstake. its the newline for the output buffer    � � � � �   t h e   l i n e   b r e a k   i n   n e x t   l i n e s   " "   i s   n o t   a   m i s s t a k e .   i t s   t h e   n e w l i n e   f o r   t h e   o u t p u t   b u f f e r �  � � � r     � � � b     � � � b     � � � o    ���� 0 
out_buffer   � o    ���� 0 theline theLine � m     � � � � �  
 � o      ���� 0 
out_buffer   �  � � � l   # � � � � r    # � � � l   ! ����� � n    ! � � � 1    !��
�� 
strq � o    ���� 0 theline theLine��  ��   � o      ���� 0 theline theLine �   make stuff console save    � � � � 0   m a k e   s t u f f   c o n s o l e   s a v e �  ��� � I  $ -�� ���
�� .sysoexecTEXT���     TEXT � b   $ ) � � � b   $ ' � � � m   $ % � � � � � 
 e c h o   � o   % &���� 0 theline theLine � m   ' ( � � � � � R   > >   ~ / L i b r a r y / L o g s / A p p l e S c r i p t - e v e n t s . l o g��  ��   �  � � � l     ��������  ��  ��   �  � � � l     �� � ���   � O I growl stuff from http://growl.info/documentation/applescript-support.php    � � � � �   g r o w l   s t u f f   f r o m   h t t p : / / g r o w l . i n f o / d o c u m e n t a t i o n / a p p l e s c r i p t - s u p p o r t . p h p �  � � � l     �� � ���   �   growl init    � � � �    g r o w l   i n i t �  � � � i   / 2 � � � I      �������� 0 
init_growl  ��  ��   � k     J � �  � � � O      � � � r     � � � ?     � � � l    ����� � I   �� ��
�� .corecnte****       ****  l   ���� 6    2    ��
�� 
prcs =    1   	 ��
�� 
bnid m     � 0 c o m . G r o w l . G r o w l H e l p e r A p p��  ��  ��  ��  ��   � m    ����   � o      ����  0 growlisrunning growlIsRunning � m     �                                                                                  sevs  alis    t  Mac                        ���H+  dրSystem Events.app                                              f ��8CW        ����  	                CoreServices    �Ϡ      �8'7    dրd�=d�<  1Mac:System:Library:CoreServices:System Events.app   $  S y s t e m   E v e n t s . a p p    M a c  -System/Library/CoreServices/System Events.app   / ��   � 	��	 Z    J
����
 o    ����  0 growlisrunning growlIsRunning O    F k   & E  l  & &����   1 + Make a list of all the notification types     � V   M a k e   a   l i s t   o f   a l l   t h e   n o t i f i c a t i o n   t y p e s    l  & &����   ' ! that this script will ever send:    � B   t h a t   t h i s   s c r i p t   w i l l   e v e r   s e n d :  r   & + J   & ) �� m   & ' �    A d d i n g   a   f i l e��   l     !����! o      ���� ,0 allnotificationslist allNotificationsList��  ��   "#" l  , ,��$%��  $ ( " Make a list of the notifications    % �&& D   M a k e   a   l i s t   o f   t h e   n o t i f i c a t i o n s  # '(' l  , ,��)*��  ) ' ! that will be enabled by default.   * �++ B   t h a t   w i l l   b e   e n a b l e d   b y   d e f a u l t .( ,-, r   , 1./. J   , /00 1��1 m   , -22 �33  A d d i n g   a   f i l e��  / l     4����4 o      ���� 40 enablednotificationslist enabledNotificationsList��  ��  - 565 l  2 2��78��  7 &   Register our script with growl.   8 �99 @   R e g i s t e r   o u r   s c r i p t   w i t h   g r o w l .6 :;: l  2 2��<=��  < ' ! for this script's notifications.   = �>> B   f o r   t h i s   s c r i p t ' s   n o t i f i c a t i o n s .; ?��? I  2 E����@
�� .registernull��� ��� null��  @ ��AB
�� 
applA l 	 4 9C����C o   4 9���� "0 scriptgrowlname scriptGrowlName��  ��  B ��DE
�� 
anotD l 
 : ;F����F o   : ;���� ,0 allnotificationslist allNotificationsList��  ��  E ��GH
�� 
dnotG o   < =���� 40 enablednotificationslist enabledNotificationsListH ��I��
�� 
iappI m   > ?JJ �KK  S c r i p t   E d i t o r��  ��   5    #��L��
�� 
cappL m     !MM �NN 0 c o m . G r o w l . G r o w l H e l p e r A p p
�� kfrmID  ��  ��  ��   � OPO l     ��QR��  Q "  growl send message function   R �SS 8   g r o w l   s e n d   m e s s a g e   f u n c t i o nP TUT i   3 6VWV I      ��X���� 0 send_growl_msg  X Y��Y o      ���� 0 
themessage  ��  ��  W Z     JZ[����Z =    \]\ o     ���� 0 send_growl_notifications  ] m    ���� [ k   
 F^^ _`_ O   
 #aba r    "cdc ?     efe l   g���g I   �~h�}
�~ .corecnte****       ****h l   i�|�{i 6   jkj 2    �z
�z 
prcsk =   lml 1    �y
�y 
bnidm m    nn �oo 0 c o m . G r o w l . G r o w l H e l p e r A p p�|  �{  �}  ��  �  f m    �x�x  d o      �w�w  0 growlisrunning growlIsRunningb m   
 pp�                                                                                  sevs  alis    t  Mac                        ���H+  dրSystem Events.app                                              f ��8CW        ����  	                CoreServices    �Ϡ      �8'7    dրd�=d�<  1Mac:System:Library:CoreServices:System Events.app   $  S y s t e m   E v e n t s . a p p    M a c  -System/Library/CoreServices/System Events.app   / ��  ` q�vq Z   $ Frs�u�tr o   $ %�s�s  0 growlisrunning growlIsRunnings O   ( Btut k   0 Avv wxw l  0 0�ryz�r  y #        Send a Notification...   z �{{ :               S e n d   a   N o t i f i c a t i o n . . .x |�q| I  0 A�p�o}
�p .notifygrnull��� ��� null�o  } �n~
�n 
name~ l 	 2 3��m�l� m   2 3�� ���  A d d i n g   a   f i l e�m  �l   �k��
�k 
titl� l 	 4 5��j�i� m   4 5�� ��� . A d d i n g   a   f i l e   t o   i T u n e s�j  �i  � �h��
�h 
desc� l 	 6 7��g�f� o   6 7�e�e 0 
themessage  �g  �f  � �d��c
�d 
appl� o   8 =�b�b "0 scriptgrowlname scriptGrowlName�c  �q  u 5   ( -�a��`
�a 
capp� m   * +�� ��� 0 c o m . G r o w l . G r o w l H e l p e r A p p
�` kfrmID  �u  �t  �v  ��  ��  U ��� l     �_���_  � !  end growl helper functions   � ��� 6   e n d   g r o w l   h e l p e r   f u n c t i o n s� ��� l     �^�]�\�^  �]  �\  � ��� l     �[���[  �   send boxcar notification   � ��� 2   s e n d   b o x c a r   n o t i f i c a t i o n� ��� i   7 :��� I      �Z��Y�Z 0 send_boxcar_msg  � ��X� o      �W�W 0 msg  �X  �Y  � k     e�� ��� r     
��� I     �V��U�V 0 replace_chars  � ��� o    �T�T 0 msg  � ��� m    �� ���   � ��S� m    �� ���  +�S  �U  � l     ��R�Q� o      �P�P 0 msg  �R  �Q  � ��� I    �O��N�O 0 	log_event  � ��M� b    ��� m    �� ��� : s e n d i n g   b o x c a r   n o t i f i c a t i o n :  � o    �L�L 0 msg  �M  �N  � ��� Q    b���� k    R�� ��� r    2��� I   0�K��J
�K .sysoexecTEXT���     TEXT� l   ,��I�H� b    ,��� b    *��� b    (��� b    &��� b     ��� b    ��� m    �� ��� $ c u r l   - S   - d   ' e m a i l =� o    �G�G 0 boxcar_user_email  � m    �� ��� L '   - d   ' & n o t i f i c a t i o n [ f r o m _ s c r e e n _ n a m e ] =� o     %�F�F "0 scriptgrowlname scriptGrowlName� m   & '�� ��� : '   - d   ' & n o t i f i c a t i o n [ m e s s a g e ] =� o   ( )�E�E 0 msg  � m   * +�� ��� '   - D -   h t t p : / / b o x c a r . i o / d e v i c e s / p r o v i d e r s / M H 0 S 7 x O F S w V L N v N h T p i C / n o t i f i c a t i o n s   - o / d e v / n u l l   |   g r e p   ' ^ S t a t u s '   |   s e d   ' s / S t a t u s : [   ] * / / g '�I  �H  �J  � o      �D�D 0 boxcarstatus boxcarStatus� ��� l  3 3�C�B�A�C  �B  �A  � ��� Z   3 I���@�?� =  3 :��� o   3 8�>�> 0 
more_debug  � m   8 9�=�= � I   = E�<��;�< 0 	log_event  � ��:� b   > A��� m   > ?�� ���  b o x c a r S t a t u s :  � o   ? @�9�9 0 boxcarstatus boxcarStatus�:  �;  �@  �?  � ��� r   J O��� c   J M��� o   J K�8�8 0 boxcarstatus boxcarStatus� m   K L�7
�7 
long� o      �6�6 0 boxcarstatus boxcarStatus� ��5� L   P R�� o   P Q�4�4 0 boxcarstatus boxcarStatus�5  � R      �3��2
�3 .ascrerr ****      � ****� o      �1�1 0 errorstr errorStr�2  � I   Z b�0��/�0 0 	log_event  � ��.� b   [ ^��� m   [ \�� ��� 4 s e n d   n o t i f i c a t i o n   f a i l e d :  � o   \ ]�-�- 0 errorstr errorStr�.  �/  � ��,� L   c e�� m   c d�+�+  �,  � ��� l     �*�)�(�*  �)  �(  � ��� l     �'���'  � Q K get the system language from http://macscripter.net/viewtopic.php?id=19528   � ��� �   g e t   t h e   s y s t e m   l a n g u a g e   f r o m   h t t p : / / m a c s c r i p t e r . n e t / v i e w t o p i c . p h p ? i d = 1 9 5 2 8� � � i   ; > I      �&�%�$�& 0 get_sys_language  �%  �$   k     
  r      I    �#�"
�# .sysoexecTEXT���     TEXT m     		 �

 � d e f a u l t s   r e a d   . G l o b a l P r e f e r e n c e s   A p p l e L a n g u a g e s   |   g r e p   - v   ' ^ ( '   |   h e a d   - n 1   |   s e d   ' s / [   , ] * / / g '�"   o      �!�!  0 systemlanguage SystemLanguage �  L    
 o    	��  0 systemlanguage SystemLanguage�      l     ����  �  �    i   ? B I      ��� 0 replace_chars    o      �� 0 	this_text    o      �� 0 search_string   � o      �� 0 replacement_string  �  �   k        r      l    �� o     �� 0 search_string  �  �   n       1    �
� 
txdl  1    �
� 
ascr !"! r    #$# n    	%&% 2    	�
� 
citm& o    �� 0 	this_text  $ l     '��' o      �� 0 	item_list  �  �  " ()( r    *+* l   ,��
, o    �	�	 0 replacement_string  �  �
  + n     -.- 1    �
� 
txdl. 1    �
� 
ascr) /0/ r    121 c    343 l   5��5 o    �� 0 	item_list  �  �  4 m    �
� 
TEXT2 o      �� 0 	this_text  0 676 r    898 m    :: �;;  9 n     <=< 1    �
� 
txdl= 1    � 
�  
ascr7 >��> L     ?? o    ���� 0 	this_text  ��   @A@ l     ��������  ��  ��  A BCB l     ��DE��  D   recursive process folder   E �FF 2   r e c u r s i v e   p r o c e s s   f o l d e rC GHG l     ��IJ��  I n h based on http://stackoverflow.com/questions/3896175/applescript-processing-files-in-folders-recursively   J �KK �   b a s e d   o n   h t t p : / / s t a c k o v e r f l o w . c o m / q u e s t i o n s / 3 8 9 6 1 7 5 / a p p l e s c r i p t - p r o c e s s i n g - f i l e s - i n - f o l d e r s - r e c u r s i v e l yH LML i   C FNON I      ��P���� 0 process_folder  P Q��Q o      ���� *0 foldernametoprocess folderNameToProcess��  ��  O k     �RR STS Z     UV����U =    WXW o     ���� 0 
more_debug  X m    ���� V I   
 ��Y���� 0 	log_event  Y Z��Z b    [\[ m    ]] �^^ 0 n o w   l o o k i n g   i n t o   f o l d e r  \ o    ���� *0 foldernametoprocess folderNameToProcess��  ��  ��  ��  T _��_ O    �`a` k    �bb cdc r    #efe n    !ghg 2    !��
�� 
fileh 4    ��i
�� 
cfoli o    ���� *0 foldernametoprocess folderNameToProcessf o      ���� 0 theitems theItemsd jkj X   $ ?l��ml n  4 :non I   5 :��p���� 0 process_file  p q��q o   5 6���� 0 thefile theFile��  ��  o  f   4 5�� 0 thefile theFilem o   ' (���� 0 theitems theItemsk rsr r   @ Jtut n   @ Hvwv 1   F H��
�� 
pnamw n   @ Fxyx 2  D F��
�� 
cfoly 4   @ D��z
�� 
cfolz o   B C���� *0 foldernametoprocess folderNameToProcessu o      ���� 0 
thefolders 
theFolderss {��{ X   K �|��}| k   [ �~~ � s   [ a��� c   [ ^��� o   [ \���� 0 	thefolder 	theFolder� m   \ ]��
�� 
TEXT� o      ���� 0 thefoldername TheFolderName� ��� r   b i��� b   b g��� b   b e��� o   b c���� *0 foldernametoprocess folderNameToProcess� m   c d�� ���  :� o   e f���� 0 thefoldername TheFolderName� o      ���� 0 
nextfolder 
nextFolder� ���� Q   j ����� n  m s��� I   n s������� 0 process_folder  � ���� o   n o���� 0 
nextfolder 
nextFolder��  ��  �  f   m n� R      �����
�� .ascrerr ****      � ****� o      ���� 0 errstr errStr��  � k   { ��� ��� n  { ���� I   | �������� 0 	log_event  � ���� m   | }�� ��� ( p r o c e s s _ f o l d e r   e r r o r��  ��  �  f   { |� ���� n  � ���� I   � �������� 0 	log_event  � ���� b   � ���� m   � ��� ���  e r r o r :  � o   � ����� 0 errstr errStr��  ��  �  f   � ���  ��  �� 0 	thefolder 	theFolder} o   N O���� 0 
thefolders 
theFolders��  a m    ���                                                                                  MACS  alis    V  Mac                        ���H+  dր
Finder.app                                                     ea�Ƙh        ����  	                CoreServices    �Ϡ      ƘK�    dրd�=d�<  *Mac:System:Library:CoreServices:Finder.app   
 F i n d e r . a p p    M a c  &System/Library/CoreServices/Finder.app  / ��  ��  M ��� l     ��������  ��  ��  � ��� l     ������  �   looking at a file   � ��� $   l o o k i n g   a t   a   f i l e� ��� l     ������  � N H basic idea from http://dougscripts.com/itunes/itinfo/folderaction01.php   � ��� �   b a s i c   i d e a   f r o m   h t t p : / / d o u g s c r i p t s . c o m / i t u n e s / i t i n f o / f o l d e r a c t i o n 0 1 . p h p� ��� l     ������  � H B and https://discussions.apple.com/thread/2489405?start=0&tstart=0   � ��� �   a n d   h t t p s : / / d i s c u s s i o n s . a p p l e . c o m / t h r e a d / 2 4 8 9 4 0 5 ? s t a r t = 0 & t s t a r t = 0� ��� i   G J��� I      ������� 0 process_file  � ���� o      ���� 
0 myfile  ��  ��  � k    y�� ��� l    ���� r     ��� l    ������ c     ��� o     ���� 
0 myfile  � m    ��
�� 
alis��  ��  � o      ���� 0 f  � 2 , i dont know what this does / why its needed   � ��� X   i   d o n t   k n o w   w h a t   t h i s   d o e s   /   w h y   i t s   n e e d e d� ��� l   ��������  ��  ��  � ��� r    ��� l   ������ n    ��� 1   	 ��
�� 
strq� l   	������ n    	��� 1    	��
�� 
psxp� o    ���� 0 f  ��  ��  ��  ��  � l     ������ o      ���� 0 	file_path  ��  ��  � ��� l   ������  � Z T the POSIX path because logging "f" does not work / crashes when the files has a ->'   � ��� �   t h e   P O S I X   p a t h   b e c a u s e   l o g g i n g   " f "   d o e s   n o t   w o r k   /   c r a s h e s   w h e n   t h e   f i l e s   h a s   a   - > '� ��� Z    $������� =   ��� o    ���� 0 
more_debug  � m    ���� � I     ������� 0 	log_event  � ���� b    ��� m    �� ���   l o o k i n g   a t   f i l e  � o    ���� 0 	file_path  ��  ��  ��  ��  � ��� O  % 3��� r   ) 2��� c   ) 0��� b   ) .��� m   ) *�� ���  .� l  * -������ n   * -��� 1   + -��
�� 
nmxt� o   * +���� 0 f  ��  ��  � m   . /��
�� 
TEXT� o      ���� "0 myitemextension myItemExtension� m   % &���                                                                                  MACS  alis    V  Mac                        ���H+  dր
Finder.app                                                     ea�Ƙh        ����  	                CoreServices    �Ϡ      ƘK�    dրd�=d�<  *Mac:System:Library:CoreServices:Finder.app   
 F i n d e r . a p p    M a c  &System/Library/CoreServices/Finder.app  / ��  � ��� l  4 4������  �   do we have a mp3 file ?   � �   0   d o   w e   h a v e   a   m p 3   f i l e   ?� �� Z   4y�� E   4 ; o   4 9���� 0 myfiletypes myFiletypes o   9 :���� "0 myitemextension myItemExtension k   >` 	 l  > >��
��  
 v p it will check if the file that was added is still beeing copied by checking the size every <DELAY_TIME_SECONDS>    � �   i t   w i l l   c h e c k   i f   t h e   f i l e   t h a t   w a s   a d d e d   i s   s t i l l   b e e i n g   c o p i e d   b y   c h e c k i n g   t h e   s i z e   e v e r y   < D E L A Y _ T I M E _ S E C O N D S >	  r   > A m   > ?����   o      ���� 0 oldsize oldSize  r   B E m   B C������ o      ���� 0 newsize newSize  l  F F����   b \ When newSize equals oldSize, it means the copy is complete because the size hasn't changed.    � �   W h e n   n e w S i z e   e q u a l s   o l d S i z e ,   i t   m e a n s   t h e   c o p y   i s   c o m p l e t e   b e c a u s e   t h e   s i z e   h a s n ' t   c h a n g e d .  V   F � k   N �   Z   N b!"����! =  N U#$# o   N S���� 0 
more_debug  $ m   S T���� " I   X ^��%���� 0 	log_event  % &��& m   Y Z'' �(( ( l o o k i n g   a t   f i l e   s i z e��  ��  ��  ��    )*) l  c c��+,��  +   Get the file size.   , �-- &   G e t   t h e   f i l e   s i z e .* ./. r   c l010 n   c j232 1   h j��
�� 
ptsz3 l  c h4����4 I  c h��5��
�� .sysonfo4asfe        file5 o   c d���� 0 f  ��  ��  ��  1 o      �� 0 oldsize oldSize/ 676 I  m v�~8�}
�~ .sysodelanull��� ��� nmbr8 o   m r�|�| (0 delay_time_seconds DELAY_TIME_SECONDS�}  7 9:9 l  w w�{;<�{  ; 8 2 Sample the size again after delay for comparison.   < �== d   S a m p l e   t h e   s i z e   a g a i n   a f t e r   d e l a y   f o r   c o m p a r i s o n .: >�z> r   w �?@? n   w ~ABA 1   | ~�y
�y 
ptszB l  w |C�x�wC I  w |�vD�u
�v .sysonfo4asfe        fileD o   w x�t�t 0 f  �u  �x  �w  @ o      �s�s 0 newsize newSize�z   >  J MEFE o   J K�r�r 0 newsize newSizeF o   K L�q�q 0 oldsize oldSize GHG Z   � �IJ�p�oI =  � �KLK o   � ��n�n 0 
more_debug  L m   � ��m�m J I   � ��lM�k�l 0 	log_event  M N�jN m   � �OO �PP 2 d o n e   l o o k i n g   a t   f i l e   s i z e�j  �k  �p  �o  H QRQ l  � ��i�h�g�i  �h  �g  R STS Z   � �UV�fWU =  � �XYX o   � ��e�e 0 enable_dialog  Y m   � ��d�d V k   � �ZZ [\[ r   � �]^] c   � �_`_ l  � �a�c�ba b   � �bcb b   � �ded b   � �fgf m   � �hh �ii & A d d   f i l e   t o   i T u n e s :g o   � ��a�a 0 	file_path  e o   � ��`
�` 
ret c o   � ��_
�_ 
ret �c  �b  ` m   � ��^
�^ 
utxt^ o      �]�] 0 alert_message  \ jkj I  � ��\lm
�\ .sysodlogaskr        TEXTl l  � �n�[�Zn o   � ��Y�Y 0 alert_message  �[  �Z  m �Xop
�X 
btnso J   � �qq rsr m   � �tt �uu  Y e ss v�Wv m   � �ww �xx  N o�W  p �Vyz
�V 
dflty m   � ��U�U z �T{|
�T 
disp{ m   � ��S�S | �R}�Q
�R 
givu} o   � ��P�P 0 dialog_timeout  �Q  k ~�O~ r   � �� l  � ���N�M� n   � ���� 1   � ��L
�L 
bhit� l  � ���K�J� 1   � ��I
�I 
rslt�K  �J  �N  �M  � l     ��H�G� o      �F�F 0 user_choice  �H  �G  �O  �f  W r   � ���� m   � ��� ���  Y e s� l     ��E�D� o      �C�C 0 user_choice  �E  �D  T ��B� Z   �`���A�@� =  � ���� o   � ��?�? 0 user_choice  � m   � ��� ���  Y e s� k   �\�� ��� l  � ��>���>  � , & HERE BEGINS THE ITUNES SPECIFIC STUFF   � ��� L   H E R E   B E G I N S   T H E   I T U N E S   S P E C I F I C   S T U F F� ��� I   � ��=��<�= 0 	log_event  � ��;� b   � ���� m   � ��� ��� . a d d i n g   f i l e   t o   i t u n e s :  � o   � ��:�: 0 	file_path  �;  �<  � ��� I   ��9��8�9 0 send_growl_msg  � ��7� o   � ��6�6 0 	file_path  �7  �8  � ��� Q  Z���� k  =�� ��� O  ��� k  �� ��� I �5�4�3
�5 .ascrnoop****      � ****�4  �3  � ��2� I �1��0
�1 .hookAdd cTrk      @ alis� o  �/�/ 0 f  �0  �2  � m  ���                                                                                  hook  alis    2  Mac                        ���H+  dֈ
iTunes.app                                                        ���Q        ����  	                Applications    �Ϡ      �i1    dֈ  Mac:Applications:iTunes.app    
 i T u n e s . a p p    M a c  Applications/iTunes.app   / ��  � ��� r  %��� [  ��� o  �.�. 0 number_of_mp3s  � m  �-�- � o      �,�, 0 number_of_mp3s  � ��+� Z  &=���*�)� = &-��� o  &+�(�( 0 delete_mp3s  � m  +,�'�' � I 09�&��%
�& .sysoexecTEXT���     TEXT� l 05��$�#� b  05��� m  03�� ���  r m   - f  � o  34�"�" 0 	file_path  �$  �#  �%  �*  �)  �+  � R      �!�� 
�! .ascrerr ****      � ****� o      �� 0 errstr errStr�   � k  EZ�� ��� I  EO���� 0 	log_event  � ��� b  FK��� m  FI�� ��� : e r r o r   a d d i n g   f i l e   t o   i t u n e s :  � o  IJ�� 0 	file_path  �  �  � ��� I  PZ���� 0 	log_event  � ��� b  QV��� m  QT�� ���  e r r o r :  � o  TU�� 0 errstr errStr�  �  �  � ��� l [[����  � * $ HERE ENDS THE ITUNES SPECIFIC STUFF   � ��� H   H E R E   E N D S   T H E   I T U N E S   S P E C I F I C   S T U F F�  �A  �@  �B  ��   Z  cy����� = cj��� o  ch�� 0 
more_debug  � m  hi�� � I  mu���� 0 	log_event  � ��� m  nq�� ���  n o t   a n   m p 3�  �  �  �  ��  � ��� l     ���
�  �  �
  � ��� l     �	���	  �  �  � ��� l     ����  �   main stuff   � ���    m a i n   s t u f f� ��� i   K N��� I      ���� 0 main  � ��� o      �� 0 root  �  �  � k    ?�� ��� l     �� ���  �   ��  � ��� I     ������� 0 	log_event  � ���� b    ��� m    �� ���  r u n n i n g  � o    ���� "0 scriptgrowlname scriptGrowlName��  ��  � ��� r    ��� m    ����  � o      ���� 0 number_of_mp3s  �    l   ����     growl stuff    �    g r o w l   s t u f f  I    �������� 0 
init_growl  ��  ��    l   ��	
��  	 9 3 this will look at all files and folder recursively   
 � f   t h i s   w i l l   l o o k   a t   a l l   f i l e s   a n d   f o l d e r   r e c u r s i v e l y  I    !������ 0 process_folder   �� o    ���� 0 root  ��  ��    l  " "��������  ��  ��    Z   " ����� =  " ) o   " '���� 0 update_match   m   ' (����  Q   , ��� k   / �  I   / 5������ 0 	log_event   �� m   0 1 �   < t e l l i n g   i t u n e s   t o   u p d a t e   m a t c h��  ��   !"! l  6 6��#$��  # %  en and default menu item names   $ �%% >   e n   a n d   d e f a u l t   m e n u   i t e m   n a m e s" &'& r   6 9()( m   6 7** �++ & U p d a t e   i T u n e s   M a t c h) o      ���� 0 match_menu_item  ' ,-, r   : =./. m   : ;00 �11 
 S t o r e/ o      ���� 0 store_menu_item  - 232 l  > >��45��  4   get system language   5 �66 (   g e t   s y s t e m   l a n g u a g e3 787 r   > E9:9 I   > C�������� 0 get_sys_language  ��  ��  : o      ���� 0 cur_lang  8 ;<; l  F F��=>��  = &   feel free to add more languages   > �?? @   f e e l   f r e e   t o   a d d   m o r e   l a n g u a g e s< @A@ Z   F WBC����B =  F IDED o   F G���� 0 cur_lang  E m   G HFF �GG  d eC k   L SHH IJI r   L OKLK m   L MMM �NN 4 i T u n e s   M a t c h   a k t u a l i s i e r e nL o      ���� 0 match_menu_item  J O��O r   P SPQP m   P QRR �SS 
 S t o r eQ o      ���� 0 store_menu_item  ��  ��  ��  A TUT O  X bVWV I  \ a������
�� .miscactvnull��� ��� null��  ��  W m   X YXX�                                                                                  hook  alis    2  Mac                        ���H+  dֈ
iTunes.app                                                        ���Q        ����  	                Applications    �Ϡ      �i1    dֈ  Mac:Applications:iTunes.app    
 i T u n e s . a p p    M a c  Applications/iTunes.app   / ��  U YZY O   c �[\[ O   g �]^] I  n ���_��
�� .prcsclicuiel    ��� uiel_ n   n �`a` 4   ~ ���b
�� 
menIb o   � ����� 0 match_menu_item  a n   n ~cdc 4   y ~��e
�� 
menEe m   | }���� d n   n yfgf 4   t y��h
�� 
mbrih o   w x���� 0 store_menu_item  g 4   n t��i
�� 
mbari m   r s���� ��  ^ 4   g k��j
�� 
pcapj m   i jkk �ll  i T u n e s\ m   c dmm�                                                                                  sevs  alis    t  Mac                        ���H+  dրSystem Events.app                                              f ��8CW        ����  	                CoreServices    �Ϡ      �8'7    dրd�=d�<  1Mac:System:Library:CoreServices:System Events.app   $  S y s t e m   E v e n t s . a p p    M a c  -System/Library/CoreServices/System Events.app   / ��  Z n��n O   � �opo r   � �qrq m   � ���
�� boovfalsr n      sts 1   � ���
�� 
pvist 4   � ���u
�� 
prcsu m   � �vv �ww  i T u n e sp m   � �xx�                                                                                  sevs  alis    t  Mac                        ���H+  dրSystem Events.app                                              f ��8CW        ����  	                CoreServices    �Ϡ      �8'7    dրd�=d�<  1Mac:System:Library:CoreServices:System Events.app   $  S y s t e m   E v e n t s . a p p    M a c  -System/Library/CoreServices/System Events.app   / ��  ��   R      ������
�� .ascrerr ****      � ****��  ��  ��  ��  ��   yzy l  � ���{|��  {   boxcar stuff   | �}}    b o x c a r   s t u f fz ~~ Z   �0������� >  � ���� o   � ����� 0 boxcar_user_email  � m   � ��� ���  � k   �,�� ��� O   � ���� r   � ���� n   � ���� 1   � ���
�� 
pnam� 4   � ����
�� 
cfol� o   � ����� 0 root  � o      ���� 0 folder_name  � m   � ����                                                                                  MACS  alis    V  Mac                        ���H+  dր
Finder.app                                                     ea�Ƙh        ����  	                CoreServices    �Ϡ      ƘK�    dրd�=d�<  *Mac:System:Library:CoreServices:Finder.app   
 F i n d e r . a p p    M a c  &System/Library/CoreServices/Finder.app  / ��  � ��� r   � ���� b   � ���� b   � ���� b   � ���� m   � ��� ���  A d d e d  � o   � ����� 0 number_of_mp3s  � m   � ��� ��� ,   s o n g s   t o   i T u n e s   f r o m  � o   � ����� 0 folder_name  � o      ���� 0 
boxcar_msg  � ��� r   � ���� I   � �������� 0 send_boxcar_msg  � ���� o   � ����� 0 
boxcar_msg  ��  ��  � o      ���� 0 boxcar_status  � ��� l  � ���������  ��  ��  � ���� Z   �,������� =  � ���� o   � ����� 0 boxcar_status  � m   � ������� k   �(�� ��� I   � �������� 0 	log_event  � ���� m   � ��� ��� T s u b s c r i b i n g   t o   b o x c a r   ' M o n i t o r i n g '   s e r v i c e��  ��  � ��� I  ������
�� .sysoexecTEXT���     TEXT� l  ������� b   ���� b   � ��� m   � ��� ���  c u r l   - d   ' e m a i l =� o   � ����� 0 boxcar_user_email  � m   �� ��� � '   h t t p : / / b o x c a r . i o / d e v i c e s / p r o v i d e r s / M H 0 S 7 x O F S w V L N v N h T p i C / n o t i f i c a t i o n s / s u b s c r i b e��  ��  ��  � ��� I 	�����
�� .sysodelanull��� ��� nmbr� m  	
���� ��  � ���� Z  (������� > ��� I  ������� 0 send_boxcar_msg  � ���� o  ���� 0 
boxcar_msg  ��  ��  � m  ���� �� I  $������� 0 	log_event  � ���� m   �� ��� � s e n d i n g   b o x c a r   n o t i f i c a t i o n   f a i l e d .   c h e c k   e m a i l   a n d   t h e   ' M o n i t o r i n g '   s e r v i c e   i n   b o x c a r��  ��  ��  ��  ��  ��  ��  ��  ��  ��   ���� I  1?������� 0 	log_event  � ���� b  2;��� o  27���� "0 scriptgrowlname scriptGrowlName� m  7:�� ��� 
   d o n e��  ��  ��  � ��� l     ��������  ��  ��  � ��� l     ������  � U O the run method. it is called when run with osascript or from the script editor   � ��� �   t h e   r u n   m e t h o d .   i t   i s   c a l l e d   w h e n   r u n   w i t h   o s a s c r i p t   o r   f r o m   t h e   s c r i p t   e d i t o r� ��� i   O R��� I     �����
�� .aevtoappnull  �   � ****� o      ���� 0 argv  ��  � k     E�� ��� r     ��� m     �� ���  � o      ���� 0 
out_buffer  � ��� Z    >������ ?    ��� l   ������ I   �����
�� .corecnte****       ****� o    	���� 0 argv  ��  ��  ��  � m    ��  � k    1�� ��� r    ��� n    ��� 4    �~�
�~ 
cobj� m    �}�} � o    �|�| 0 argv  � o      �{�{ 0 pathtoprocess pathToProcess� ��� I    !�z��y�z 0 	log_event  � ��x� b    ��� m    �� ��� , c a l l e d   w i t h   a r g u m e n t :  � o    �w�w 0 pathtoprocess pathToProcess�x  �y  �    r   " * c   " ( 4   " &�v
�v 
psxf o   $ %�u�u 0 pathtoprocess pathToProcess m   & '�t
�t 
TEXT o      �s�s 0 pathtoprocess pathToProcess �r I   + 1�q�p�q 0 main   	�o	 o   , -�n�n 0 pathtoprocess pathToProcess�o  �p  �r  ��  � k   4 >

  l  4 4�m�m     test function    �    t e s t   f u n c t i o n �l I   4 >�k�j�k 0 main   �i o   5 :�h�h 0 test_folder  �i  �j  �l  � �g L   ? E o   ? D�f�f 0 
out_buffer  �g  �  l     �e�d�c�e  �d  �c    l     �b�b     folder action "hook"    � *   f o l d e r   a c t i o n   " h o o k "  l     �a�a   _ Y this can also be used as folder action � it will always look at everything in that foler    �   �   t h i s   c a n   a l s o   b e   u s e d   a s   f o l d e r   a c t i o n   &   i t   w i l l   a l w a y s   l o o k   a t   e v e r y t h i n g   i n   t h a t   f o l e r !"! i   S V#$# I     �`%&
�` .facofgetnull���     alis% o      �_�_ 0 
thisfolder 
thisFolder& �^'�]
�^ 
flst' o      �\�\ 0 theitems theItems�]  $ k     (( )*) r     +,+ m     -- �..  , o      �[�[ 0 
out_buffer  * /�Z/ I    �Y0�X�Y 0 main  0 1�W1 o   	 
�V�V 0 
thisfolder 
thisFolder�W  �X  �Z  " 2�U2 l     �T�S�R�T  �S  �R  �U       2�Q3�P�O�N R�M4�L�K w�J5�I �6789:;<=>?@A�H�G�F�E�D�C�B�A�@�?�>�=�<�;�:�9�8�7�6�5�4�3�2�Q  3 0�1�0�/�.�-�,�+�*�)�(�'�&�%�$�#�"�!� ����������������������
�	��������1 0 update_match  �0 0 delete_mp3s  �/ 0 send_growl_notifications  �. 0 boxcar_user_email  �- (0 delay_time_seconds DELAY_TIME_SECONDS�, 0 myfiletypes myFiletypes�+ 0 enable_dialog  �* 0 dialog_timeout  �) 0 test_folder  �( 0 
more_debug  �' 0 
out_buffer  �& 0 number_of_mp3s  �% "0 scriptgrowlname scriptGrowlName�$ 0 	log_event  �# 0 
init_growl  �" 0 send_growl_msg  �! 0 send_boxcar_msg  �  0 get_sys_language  � 0 replace_chars  � 0 process_folder  � 0 process_file  � 0 main  
� .aevtoappnull  �   � ****
� .facofgetnull���     alis� 0 pathtoprocess pathToProcess�  �  �  �  �  �  �  �  �  �  �  �  �  �  �
  �	  �  �  �  �  �  �  �  �P �O �N  �M 4 �B� B   a�L  �K �J  5 �CC� 2 0 1 3 - 0 5 - 0 7   0 8 : 4 0 : 5 9   c a l l e d   w i t h   a r g u m e n t :   / U s e r s / l a d / A z u r e u s / s a b n z b d / M u s i c / D u h   ( X D M . 1 1 4 1 - 8 ) 
 2 0 1 3 - 0 5 - 0 7   0 8 : 4 0 : 5 9   r u n n i n g   A d d   m p 3 s   t o   i T u n e s   s c r i p t 
 2 0 1 3 - 0 5 - 0 7   0 8 : 4 1 : 1 5   a d d i n g   f i l e   t o   i t u n e s :   ' / U s e r s / l a d / A z u r e u s / s a b n z b d / M u s i c / D u h   ( X D M . 1 1 4 1 - 8 ) / 0 1 - l a g w a g o n - t r a g i c _ v i s i o n - e o s . m p 3 ' 
 2 0 1 3 - 0 5 - 0 7   0 8 : 4 1 : 1 9   a d d i n g   f i l e   t o   i t u n e s :   ' / U s e r s / l a d / A z u r e u s / s a b n z b d / M u s i c / D u h   ( X D M . 1 1 4 1 - 8 ) / 0 2 - l a g w a g o n - f o i l e d _ a g a i n - e o s . m p 3 ' 
 2 0 1 3 - 0 5 - 0 7   0 8 : 4 1 : 2 3   a d d i n g   f i l e   t o   i t u n e s :   ' / U s e r s / l a d / A z u r e u s / s a b n z b d / M u s i c / D u h   ( X D M . 1 1 4 1 - 8 ) / 0 3 - l a g w a g o n - b u r y _ t h e _ h a t c h e t - e o s . m p 3 ' 
 2 0 1 3 - 0 5 - 0 7   0 8 : 4 1 : 2 6   a d d i n g   f i l e   t o   i t u n e s :   ' / U s e r s / l a d / A z u r e u s / s a b n z b d / M u s i c / D u h   ( X D M . 1 1 4 1 - 8 ) / 0 4 - l a g w a g o n - a n g r y _ d a y s - e o s . m p 3 ' 
 2 0 1 3 - 0 5 - 0 7   0 8 : 4 1 : 3 0   a d d i n g   f i l e   t o   i t u n e s :   ' / U s e r s / l a d / A z u r e u s / s a b n z b d / M u s i c / D u h   ( X D M . 1 1 4 1 - 8 ) / 0 5 - l a g w a g o n - n o b l e _ e n d - e o s . m p 3 ' 
 2 0 1 3 - 0 5 - 0 7   0 8 : 4 1 : 3 4   a d d i n g   f i l e   t o   i t u n e s :   ' / U s e r s / l a d / A z u r e u s / s a b n z b d / M u s i c / D u h   ( X D M . 1 1 4 1 - 8 ) / 0 6 - l a g w a g o n - c h i l d _ i n s i d e - e o s . m p 3 ' 
 2 0 1 3 - 0 5 - 0 7   0 8 : 4 1 : 3 8   a d d i n g   f i l e   t o   i t u n e s :   ' / U s e r s / l a d / A z u r e u s / s a b n z b d / M u s i c / D u h   ( X D M . 1 1 4 1 - 8 ) / 0 7 - l a g w a g o n - b a d _ m o o n _ r i s i n g - e o s . m p 3 ' 
 2 0 1 3 - 0 5 - 0 7   0 8 : 4 1 : 4 2   a d d i n g   f i l e   t o   i t u n e s :   ' / U s e r s / l a d / A z u r e u s / s a b n z b d / M u s i c / D u h   ( X D M . 1 1 4 1 - 8 ) / 0 8 - l a g w a g o n - b e e r _ g o g g l e s - e o s . m p 3 ' 
 2 0 1 3 - 0 5 - 0 7   0 8 : 4 1 : 4 6   a d d i n g   f i l e   t o   i t u n e s :   ' / U s e r s / l a d / A z u r e u s / s a b n z b d / M u s i c / D u h   ( X D M . 1 1 4 1 - 8 ) / 0 9 - l a g w a g o n - i n s p e c t o r _ g a d g e t - e o s . m p 3 ' 
 2 0 1 3 - 0 5 - 0 7   0 8 : 4 1 : 5 0   a d d i n g   f i l e   t o   i t u n e s :   ' / U s e r s / l a d / A z u r e u s / s a b n z b d / M u s i c / D u h   ( X D M . 1 1 4 1 - 8 ) / 1 0 - l a g w a g o n - p a r e n t s _ g u i d e _ t o _ l i v i n g - e o s . m p 3 ' 
 2 0 1 3 - 0 5 - 0 7   0 8 : 4 1 : 5 4   a d d i n g   f i l e   t o   i t u n e s :   ' / U s e r s / l a d / A z u r e u s / s a b n z b d / M u s i c / D u h   ( X D M . 1 1 4 1 - 8 ) / 1 1 - l a g w a g o n - m r _ c o f f e e - e o s . m p 3 ' 
 2 0 1 3 - 0 5 - 0 7   0 8 : 4 1 : 5 8   a d d i n g   f i l e   t o   i t u n e s :   ' / U s e r s / l a d / A z u r e u s / s a b n z b d / M u s i c / D u h   ( X D M . 1 1 4 1 - 8 ) / 1 2 - l a g w a g o n - o f _ m i n d _ a n d _ m a t t e r - e o s . m p 3 ' 
 2 0 1 3 - 0 5 - 0 7   0 8 : 4 2 : 0 2   a d d i n g   f i l e   t o   i t u n e s :   ' / U s e r s / l a d / A z u r e u s / s a b n z b d / M u s i c / D u h   ( X D M . 1 1 4 1 - 8 ) / 1 3 - l a g w a g o n - s t o p _ w h i n i n g - e o s . m p 3 ' 
 2 0 1 3 - 0 5 - 0 7   0 8 : 4 2 : 0 6   a d d i n g   f i l e   t o   i t u n e s :   ' / U s e r s / l a d / A z u r e u s / s a b n z b d / M u s i c / D u h   ( X D M . 1 1 4 1 - 8 ) / 1 4 - l a g w a g o n - l a g _ w a g o n - e o s . m p 3 ' 
 2 0 1 3 - 0 5 - 0 7   0 8 : 4 2 : 0 6   t e l l i n g   i t u n e s   t o   u p d a t e   m a t c h 
 2 0 1 3 - 0 5 - 0 7   0 8 : 4 2 : 0 9   s e n d i n g   b o x c a r   n o t i f i c a t i o n :   A d d e d + 1 4 + s o n g s + t o + i T u n e s + f r o m + D u h + ( X D M . 1 1 4 1 - 8 ) 
 2 0 1 3 - 0 5 - 0 7   0 8 : 4 2 : 1 0   A d d   m p 3 s   t o   i T u n e s   s c r i p t   d o n e 
�I 6 �  �����DE���  0 	log_event  �� ��F�� F  ���� 0 
themessage  ��  D ������ 0 
themessage  �� 0 theline theLineE 	 ������� � ��� � �
�� 
rtyp
�� 
TEXT
�� .sysoexecTEXT���     TEXT
�� 
strq�� .���l �%�%E�Ob  
�%�%Ec  
O��,E�O�%�%j 7 �� �����GH���� 0 
init_growl  ��  ��  G ��������  0 growlisrunning growlIsRunning�� ,0 allnotificationslist allNotificationsList�� 40 enablednotificationslist enabledNotificationsListH ��I������M��2��������J����
�� 
prcsI  
�� 
bnid
�� .corecnte****       ****
�� 
capp
�� kfrmID  
�� 
appl
�� 
anot
�� 
dnot
�� 
iapp�� 
�� .registernull��� ��� null�� K� *�-�[�,\Z�81j jE�UO� -)���0 !�kvE�O�kvE�O*�b  �����a  UY h8 ��W����JK���� 0 send_growl_msg  �� ��L�� L  ���� 0 
themessage  ��  J ������ 0 
themessage  ��  0 growlisrunning growlIsRunningK p��I��n���������������������
�� 
prcs
�� 
bnid
�� .corecnte****       ****
�� 
capp
�� kfrmID  
�� 
name
�� 
titl
�� 
desc
�� 
appl�� 
�� .notifygrnull��� ��� null�� Kb  k  A� *�-�[�,\Z�81j jE�UO� )���0 *�������b  � UY hY h9 �������MN���� 0 send_boxcar_msg  �� ��O�� O  ���� 0 msg  ��  M �������� 0 msg  �� 0 boxcarstatus boxcarStatus�� 0 errorstr errorStrN ����������������������� 0 replace_chars  �� 0 	log_event  
�� .sysoexecTEXT���     TEXT
�� 
long�� 0 errorstr errorStr��  �� f*���m+ E�O*�%k+ O @�b  %�%b  %�%�%�%j 	E�Ob  	k  *�%k+ Y hO��&E�O�W X  *�%k+ Oj: ������PQ���� 0 get_sys_language  ��  ��  P ����  0 systemlanguage SystemLanguageQ 	��
�� .sysoexecTEXT���     TEXT�� �j E�O�; ������RS���� 0 replace_chars  �� ��T�� T  �������� 0 	this_text  �� 0 search_string  �� 0 replacement_string  ��  R ���������� 0 	this_text  �� 0 search_string  �� 0 replacement_string  �� 0 	item_list  S ��������:
�� 
ascr
�� 
txdl
�� 
citm
�� 
TEXT�� !���,FO��-E�O���,FO��&E�O���,FO�< ��O����UV���� 0 process_folder  �� ��W�� W  ���� *0 foldernametoprocess folderNameToProcess��  U ������������������ *0 foldernametoprocess folderNameToProcess�� 0 theitems theItems�� 0 thefile theFile�� 0 
thefolders 
theFolders�� 0 	thefolder 	theFolder�� 0 thefoldername TheFolderName�� 0 
nextfolder 
nextFolder�� 0 errstr errStrV ]������������������������������ 0 	log_event  
�� 
cfol
�� 
file
�� 
kocl
�� 
cobj
�� .corecnte****       ****�� 0 process_file  
�� 
pnam
�� 
TEXT�� 0 process_folder  �� 0 errstr errStr��  �� �b  	k  *�%k+ Y hO� x*�/�-E�O �[��l kh )�k+ [OY��O*�/�-�,E�O E�[��l kh ��&EQ�O��%�%E�O )�k+ W X  )�k+ O)a �%k+ [OY��U= �������XY���� 0 process_file  �� ��Z�� Z  ���� 
0 myfile  ��  X 	�������������������� 
0 myfile  �� 0 f  �� 0 	file_path  �� "0 myitemextension myItemExtension�� 0 oldsize oldSize�� 0 newsize newSize�� 0 alert_message  �� 0 user_choice  �� 0 errstr errStrY )�������~���}�|'�{�z�yOh�x�w�vtw�u�t�s�r�q�p�o����n��m�l��k�j�i���
�� 
alis
�� 
psxp
� 
strq�~ 0 	log_event  
�} 
nmxt
�| 
TEXT
�{ .sysonfo4asfe        file
�z 
ptsz
�y .sysodelanull��� ��� nmbr
�x 
ret 
�w 
utxt
�v 
btns
�u 
dflt
�t 
disp
�s 
givu�r 
�q .sysodlogaskr        TEXT
�p 
rslt
�o 
bhit�n 0 send_growl_msg  
�m .ascrnoop****      � ****
�l .hookAdd cTrk      @ alis
�k .sysoexecTEXT���     TEXT�j 0 errstr errStr�i  ��z��&E�O��,�,E�Ob  	k  *�%k+ Y hO� ��,%�&E�UOb  �'jE�OiE�O >h��b  	k  *�k+ Y hO�j 
�,E�Ob  j O�j 
�,E�[OY��Ob  	k  *�k+ Y hOb  k  ?�%�%�%a &E�O�a a a lva la ka b  a  O_ a ,E�Y a E�O�a   q*a �%k+ O*�k+ O =a  *j  O�j !UOb  kEc  Ob  k  a "�%j #Y hW X $ %*a &�%k+ O*a '�%k+ OPY hY b  	k  *a (k+ Y h> �h��g�f[\�e�h 0 main  �g �d]�d ]  �c�c 0 root  �f  [ �b�a�`�_�^�]�\�b 0 root  �a 0 match_menu_item  �` 0 store_menu_item  �_ 0 cur_lang  �^ 0 folder_name  �] 0 
boxcar_msg  �\ 0 boxcar_status  \ *��[�Z�Y*0�XFMRX�Wm�Vk�U�T�S�R�Q�Pv�O�N�M���L�K���J�I����H�G�F���[ 0 	log_event  �Z 0 
init_growl  �Y 0 process_folder  �X 0 get_sys_language  
�W .miscactvnull��� ��� null
�V 
pcap
�U 
mbar
�T 
mbri
�S 
menE
�R 
menI
�Q .prcsclicuiel    ��� uiel
�P 
prcs
�O 
pvis�N  �M  
�L 
cfol
�K 
pnam�J 0 send_boxcar_msg  �I�
�H .sysoexecTEXT���     TEXT
�G .sysodelanull��� ��� nmbr�F ��e@*�b  %k+ OjEc  O*j+ O*�k+ Ob   k   s*�k+ O�E�O�E�O*j+ E�O��  �E�O�E�Y hO� *j UO� #*��/ *a k/a �/a k/a �/j UUO� f*a a /a ,FUW X  hY hOb  a  za  *a �/a ,E�UOa b  %a %�%E�O*�k+  E�O�a !  ?*a "k+ Oa #b  %a $%j %Omj &O*�k+  a ' *a (k+ Y hY hY hO*b  a )%k+ ? �E��D�C^_�B
�E .aevtoappnull  �   � ****�D 0 argv  �C  ^ �A�A 0 argv  _ 	��@�?�>��=�<�;�:
�@ .corecnte****       ****
�? 
cobj�> 0 pathtoprocess pathToProcess�= 0 	log_event  
�< 
psxf
�; 
TEXT�: 0 main  �B F�Ec  
O�j j $��k/E�O*��%k+ O*��/�&E�O*�k+ Y *b  k+ Ob  
@ �9$�8�7`a�6
�9 .facofgetnull���     alis�8 0 
thisfolder 
thisFolder�7 �5�4�3
�5 
flst�4 0 theitems theItems�3  ` �2�1�2 0 
thisfolder 
thisFolder�1 0 theitems theItemsa -�0�0 0 main  �6 �Ec  
O*�k+ A �bb h M a c : U s e r s : l a d : A z u r e u s : s a b n z b d : M u s i c : D u h   ( X D M . 1 1 4 1 - 8 )�H  �G  �F  �E  �D  �C  �B  �A  �@  �?  �>  �=  �<  �;  �:  �9  �8  �7  �6  �5  �4  �3  �2   ascr  ��ޭ