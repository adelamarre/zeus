# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['venom'],
             pathex=['/home/serveurspotify/zeus'],
             binaries=[],
             datas=[],
             hiddenimports=[
                 'src.application.db.revision.revision-001',
                 'src.application.db.revision.revision-002',
                 
                 'src.application.spotify.scenario.monitor',
                 'src.application.spotify.scenario.listener',
                 'src.application.spotify.scenario.register',
                 'src.application.spotify.scenario.service',
                 
                 'src.application.system.scenario.migration',
                 'src.application.system.scenario.backup',
                 'src.application.system.scenario.admin',
                 'src.application.system.scenario.collector',
                 'src.application.system.scenario.config',
                 'src.application.system.scenario.service-config',
            ],
             hookspath=['/home/serveurspotify/zeus/pihooks'],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='venom',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
