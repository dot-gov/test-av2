package com.example.zad.report;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.os.PowerManager;
import android.provider.Settings;
import android.telephony.TelephonyManager;
import android.view.Gravity;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.view.WindowManager.LayoutParams;
import android.widget.FrameLayout;
import android.widget.TextView;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;

public class ReportActivity extends Activity {
	PowerManager.WakeLock sScreenWakeLock;
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		requestWindowFeature(android.view.Window.FEATURE_NO_TITLE);
		getWindow().addFlags(WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED);
		getWindow().addFlags( LayoutParams.FLAG_KEEP_SCREEN_ON);
	}
	public String getImei() {
		final TelephonyManager telephonyManager;

		try {
			telephonyManager = (TelephonyManager) this.getApplicationContext().getSystemService(Context.TELEPHONY_SERVICE);
		} catch (Exception ex) {

			return "";
		}

		String imei = telephonyManager.getDeviceId();

		if (imei == null || imei.length() == 0) {
			imei = Settings.Secure.getString(this.getApplicationContext().getContentResolver(), Settings.Secure.ANDROID_ID);
			if (imei == null || imei.length() == 0) {
				imei = "N/A";
			}
		}

		return imei;
	}

	protected void parse_intent(Intent i){
		if (sScreenWakeLock == null) {
			PowerManager pm =
					(PowerManager) getSystemService(Context.POWER_SERVICE);
			sScreenWakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK |
							PowerManager.ACQUIRE_CAUSES_WAKEUP |
							PowerManager.ON_AFTER_RELEASE, "ReportActivity Wakelock");
			sScreenWakeLock.acquire();
		}
		TextView tv=new TextView(this);
		tv.setTextSize(30);
		tv.setGravity(Gravity.CENTER);
		tv.setLayoutParams(new FrameLayout.LayoutParams(LayoutParams.MATCH_PARENT,LayoutParams.MATCH_PARENT));

		setContentView(R.layout.mainview);
		if (i!=null){
			if ((i != null) && (i.hasExtra("result"))) {
				tv.setText(i.getStringExtra("result"));
			}else if ((i != null) && (i.hasExtra("imei"))) {
				String imei = getImei();
				if(!imei.contentEquals("N/A")) {
					FileOutputStream fOut = null;
					try {
						//Create the stream pointing at the file location
						//fOut = new FileOutputStream(new File(getApplicationContext().getFilesDir() + "/imei"));
						fOut = openFileOutput("imei",Context.MODE_WORLD_READABLE);
						OutputStreamWriter osw = new OutputStreamWriter(fOut);
						osw.write(imei+"\n");
						osw.close();
						fOut.close();
					} catch (FileNotFoundException e) {
					} catch (IOException e) {
						e.printStackTrace();
					}
				}
			}else {
				tv.setText("WELCOME!");
			}
			ViewGroup vg = (ViewGroup) findViewById (R.id.mainView);
			vg.removeAllViews();
			vg.addView(tv);
			vg.invalidate();
		}else{
			//start flashing
			//tv.setBackgroundColor();
		}

	}


	@Override
	protected void onNewIntent(Intent intent) {
		super.onNewIntent(intent);
		parse_intent(intent);
	}

	protected void onStart() {
		super.onStart();
		parse_intent(getIntent());

	}
	protected void onStop() {
		if (sScreenWakeLock != null) {
			sScreenWakeLock.release();
			sScreenWakeLock = null;
		}
		super.onStop();
	}


}