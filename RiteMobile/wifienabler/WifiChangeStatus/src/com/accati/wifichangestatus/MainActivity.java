package com.accati.wifichangestatus;

import android.app.Activity;
import android.content.Context;
import android.net.wifi.WifiManager;
import android.os.Bundle;

public class MainActivity extends Activity {

	@Override
	public void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_main);
		WifiManager wfm = (WifiManager) getSystemService(Context.WIFI_SERVICE);
		String wifi = getIntent().getStringExtra("wifi");
		boolean sw = false;
		boolean ret;
		try {
			if (wifi != null)
				sw = Boolean.parseBoolean(wifi);
			ret = wfm.setWifiEnabled(sw);

		} catch (Exception e) {
			ret = wfm.setWifiEnabled(false);
		}
		System.exit(0);
	}
}